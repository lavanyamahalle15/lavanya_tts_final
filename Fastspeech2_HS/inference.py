import argparse
import torch
from espnet2.bin.tts_inference import Text2Speech
from hifigan.models import Generator
from scipy.io.wavfile import write
from hifigan.meldataset import MAX_WAV_VALUE
from hifigan.env import AttrDict
import yaml
from text_preprocess_for_inference import TTSDurAlignPreprocessor
import logging
import sys
import os

# Ensure log directory exists and set correct log file path
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "access.log")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
    ]
)
sys.stdout = open(log_file, "a")
sys.stderr = open(log_file, "a")

# Configure logging
logger = logging.getLogger(__name__)

def ensure_absolute_path(path):
    # Always resolve relative to the script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir, path))

def get_language_family(language):
    aryan = {'hindi', 'marathi', 'punjabi', 'gujarati', 'bengali', 'odia', 'assamese', 'bodo', 'rajasthani', 'urdu'}
    dravidian = {'tamil', 'telugu', 'kannada', 'malayalam'}
    if language.lower() in aryan:
        return 'aryan'
    elif language.lower() in dravidian:
        return 'dravidian'
    else:
        return 'aryan'  # default

def get_model_path(*parts):
    base = os.environ.get("TTS_MODEL_ROOT", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

def resolve_model_file(config_path, filename):
    """
    Resolve a model/statistics file path using TTS_MODEL_ROOT and the config.yaml directory.
    """
    import os
    model_root = os.environ.get("TTS_MODEL_ROOT", os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.dirname(config_path)
    # Prefer TTS_MODEL_ROOT if set, else config_dir
    return os.path.join(model_root, os.path.relpath(config_dir, model_root), filename)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_text', required=True)
    parser.add_argument('--language', required=True)
    parser.add_argument('--gender', required=True)
    parser.add_argument('--alpha', type=float, default=1.0)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")

        # Ensure output directory exists
        output_dir = os.path.dirname(args.output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # Load vocoder configuration
        language_family = get_language_family(args.language)
        vocoder_config = os.path.join('vocoder', args.gender, language_family, 'hifigan', 'config.json')
        vocoder_generator = os.path.join('vocoder', args.gender, language_family, 'hifigan', 'generator')
        vocoder_config = ensure_absolute_path(vocoder_config)
        vocoder_generator = ensure_absolute_path(vocoder_generator)
        if not os.path.exists(vocoder_config):
            raise FileNotFoundError(f"Vocoder config not found at {vocoder_config}")
        if not os.path.exists(vocoder_generator):
            raise FileNotFoundError(f"Vocoder generator not found at {vocoder_generator}")

        # Load configuration
        with open(vocoder_config) as f:
            data = f.read()
        json_config = yaml.safe_load(data)
        h = AttrDict(json_config)

        # Load generator
        generator = Generator(h)
        state_dict_g = torch.load(vocoder_generator, device)
        generator.load_state_dict(state_dict_g['generator'])
        generator.eval()
        generator.remove_weight_norm()
        generator = generator.to(device)

        # Process text
        logger.info(f"language {args.language}")
        preprocessor = TTSDurAlignPreprocessor()
        phone_dictionary = {}
        preprocessed_text, phrases = preprocessor.preprocess(args.sample_text, args.language, args.gender, phone_dictionary)
        preprocessed_text = " ".join(preprocessed_text)

        # Load TTS model
        model_dir = get_model_path(args.language, args.gender, "model")
        config_path = os.path.join(model_dir, "config.yaml")
        model_file = os.path.join(model_dir, "model.pth")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Model config not found at {config_path}")
        if not os.path.exists(model_file):
            raise FileNotFoundError(f"Model weights not found at {model_file}")
        # Patch config.yaml stats_file entries to absolute path using resolve_model_file
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        # Patch all *_normalize_conf: stats_file entries
        for key in ["normalize_conf", "energy_normalize_conf", "pitch_normalize_conf"]:
            if key in config_data and "stats_file" in config_data[key]:
                stats_file = config_data[key]["stats_file"]
                abs_path = resolve_model_file(config_path, stats_file)
                config_data[key]["stats_file"] = abs_path
                print(f"Patched {key} stats_file: {abs_path}")
        # Save patched config to a temp file
        import tempfile
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml') as tmpf:
            yaml.safe_dump(config_data, tmpf)
            patched_config_path = tmpf.name
        print(f"Using patched config: {patched_config_path}")
        text2speech = Text2Speech(patched_config_path, model_file)
        text2speech.device = device

        # Generate speech
        logger.info("Generating speech...")
        with torch.no_grad():
            out = text2speech(preprocessed_text, decode_conf={"alpha": args.alpha})
            x = out["feat_gen_denorm"].T.unsqueeze(0) * 2.3262
            x = x.to(device)
            y_g_hat = generator(x)
            audio = y_g_hat.squeeze()
            audio = audio * MAX_WAV_VALUE
            audio = audio.cpu().numpy().astype('int16')

            # Save the audio file
            output_path = ensure_absolute_path(args.output_file)
            write(output_path, 22050, audio)
            logger.info(f"Audio saved to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        raise

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        exit(1)
