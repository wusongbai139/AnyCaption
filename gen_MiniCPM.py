import os
import sys
import torch
from PIL import Image, UnidentifiedImageError
from transformers import AutoModel, AutoTokenizer, MBartForConditionalGeneration, MBart50TokenizerFast
import shutil
from tqdm import tqdm

caption_model_path = './MiniCPM-V-2_6'
translation_model_path = './mbart-large-50-many-to-many-mmt'

try:
    caption_model = AutoModel.from_pretrained(caption_model_path, trust_remote_code=True, attn_implementation='sdpa', torch_dtype=torch.bfloat16).eval().cuda()
    caption_tokenizer = AutoTokenizer.from_pretrained(caption_model_path, trust_remote_code=True)
except Exception as e:
    sys.exit(1)

try:
    translation_model = MBartForConditionalGeneration.from_pretrained(translation_model_path)
    translation_tokenizer = MBart50TokenizerFast.from_pretrained(translation_model_path)
except Exception as e:
    sys.exit(1)

def handle_error(image_path, error_message):
    shutil.move(image_path, os.path.join("error_img", os.path.basename(image_path)))

def generate_caption(image_path, question):
    try:
        image = Image.open(image_path).convert("RGB")
    except UnidentifiedImageError:
        handle_error(image_path, "Unable to open image")
        return None

    msgs = [{'role': 'user', 'content': [image, question]}]
    answer = caption_model.chat(image=None, msgs=msgs, tokenizer=caption_tokenizer)
    return answer.strip()

def translate_caption(text, target_language_code):
    encoded_text = translation_tokenizer(text, return_tensors="pt")
    generated_tokens = translation_model.generate(
        **encoded_text,
        forced_bos_token_id=translation_tokenizer.lang_code_to_id[target_language_code]
    )
    return translation_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

def save_caption(image_path, caption):
    text_file_path = os.path.splitext(image_path)[0] + '.txt'
    with open(text_file_path, 'w', encoding='utf-8') as text_file:
        text_file.write(caption)

def process_single_image(image_path, question, label_language, trigger_word):
    try:
        caption = generate_caption(image_path, question)
        if not caption:
            return
        if label_language != "en_XX":
            caption = translate_caption(caption, label_language)
        if trigger_word:
            caption = f"{trigger_word}, {caption}"
        save_caption(image_path, caption)
    except Exception as e:
        handle_error(image_path, str(e))

def process_images(folder_path, question, label_language, trigger_word):
    error_folder = os.path.join(folder_path, "error_img")
    os.makedirs(error_folder, exist_ok=True)
    
    all_image_files = []
    for root, _, files in os.walk(folder_path):
        all_image_files.extend(
            [os.path.join(root, file) for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        )
    total_files = len(all_image_files)
    
    with tqdm(total=total_files, desc="Processing Images", leave=True) as pbar:
        for image_path in all_image_files:
            process_single_image(image_path, question, label_language, trigger_word)
            pbar.update(1)

def main():
    if len(sys.argv) < 4:
        print("Usage: python gen_MiniCPM.py <folder_path> <question> <label_language>  [<trigger_word>]")
        sys.exit(1)

    folder_path = sys.argv[1]
    question = sys.argv[2]  # 问题由命令行参数传递
    label_language = sys.argv[3]
    trigger_word = sys.argv[4] if len(sys.argv) > 4 else ""

    process_images(folder_path, question, label_language, trigger_word)

if __name__ == "__main__":
    main()