import os
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_absolute_path(path):
    """Convert relative path to absolute path based on script location"""
    if not os.path.isabs(path):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
    return path

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

        # Ensure output directory exists with proper permissions
        output_dir = os.path.dirname(args.output_file)
        os.makedirs(output_dir, mode=0o777, exist_ok=True)
        
        # Load vocoder configuration
        vocoder_config = 'vocoder/config.json'
        vocoder_generator = f'vocoder/{args.language}/{args.gender}/generator'
        
        vocoder_config = ensure_absolute_path(vocoder_config)
        vocoder_generator = ensure_absolute_path(vocoder_generator)

        if not os.path.exists(vocoder_config):
            raise FileNotFoundError(f"Vocoder config not found at {vocoder_config}")
        if not os.path.exists(vocoder_generator):
            raise FileNotFoundError(f"Vocoder generator not found at {vocoder_generator}")

        logger.info("Loading configuration...")
        with open(vocoder_config) as f:
            data = f.read()
        json_config = yaml.safe_load(data)
        h = AttrDict(json_config)

        logger.info("Loading generator...")
        generator = Generator(h)
        state_dict_g = torch.load(vocoder_generator, map_location=device)
        generator.load_state_dict(state_dict_g['generator'])
        generator.eval()
        generator.remove_weight_norm()
        generator = generator.to(device)

        logger.info(f"Processing text for language: {args.language}")
        preprocessor = TTSDurAlignPreprocessor()
        preprocessed_text, phrases = preprocessor.preprocess(args.sample_text, args.language, args.gender)
        preprocessed_text = " ".join(preprocessed_text)

        # Load TTS model
        model_path = f"{args.language}/{args.gender}/model"
        model_path = ensure_absolute_path(model_path)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        logger.info("Loading Text2Speech model...")
        text2speech = Text2Speech(model_path)
        text2speech.device = device

        logger.info("Generating speech...")
        with torch.no_grad():
            out = text2speech(preprocessed_text, decode_conf={"alpha": args.alpha})
            x = out["feat_gen_denorm"].T.unsqueeze(0) * 2.3262
            x = x.to(device)
            y_g_hat = generator(x)
            audio = y_g_hat.squeeze()
            audio = audio * MAX_WAV_VALUE
            audio = audio.cpu().numpy().astype('int16')

            # Save the audio file with proper permissions
            output_path = ensure_absolute_path(args.output_file)
            write(output_path, 22050, audio)
            os.chmod(output_path, 0o666)  # Make file readable/writable
            logger.info(f"Audio saved to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
