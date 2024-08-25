import os
import shutil
from tqdm import tqdm
from PIL import Image, UnidentifiedImageError
from transformers import AutoProcessor, AutoModelForCausalLM, MBartForConditionalGeneration, MBart50TokenizerFast
import sys

caption_model_path = './Florence_2_large'
translation_model_path = './mbart-large-50-many-to-many-mmt'

try:
    caption_model = AutoModelForCausalLM.from_pretrained(caption_model_path, trust_remote_code=True, revision="main").eval().cuda()
    caption_processor = AutoProcessor.from_pretrained(caption_model_path, trust_remote_code=True, revision="main")
except Exception as e:
    sys.exit(1)

try:
    translation_model = MBartForConditionalGeneration.from_pretrained(translation_model_path, revision="main")
    translation_tokenizer = MBart50TokenizerFast.from_pretrained(translation_model_path, revision="main")
    translation_tokenizer.src_lang = "en_XX"
except Exception as e:
    sys.exit(1)

def handle_error(image_path, error_message):
    shutil.move(image_path, os.path.join("error_img", os.path.basename(image_path)))

def generate_caption(task_prompt, image_path):
    try:
        image = Image.open(image_path).convert("RGB")
    except UnidentifiedImageError:
        handle_error(image_path, "Unable to open image")
        return None

    inputs = caption_processor(text=task_prompt, images=image, return_tensors="pt")
    generated_ids = caption_model.generate(
        input_ids=inputs["input_ids"].cuda(),
        pixel_values=inputs["pixel_values"].cuda(),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
    )
    generated_text = caption_processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = caption_processor.post_process_generation(
        generated_text, 
        task=task_prompt, 
        image_size=(image.width, image.height)
    )
    return parsed_answer[task_prompt].strip()

def translate_to_target_language(text, target_language_code):
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

def process_single_image(image_path, task_prompt, caption_type, additional_tags):
    try:
        caption = generate_caption(task_prompt, image_path)
        if caption is None:
            return
        if caption_type != "EN":
            caption = translate_to_target_language(caption, caption_type)
        if additional_tags:
            caption = f"{additional_tags}, {caption}"
        save_caption(image_path, caption)
    except Exception as e:
        handle_error(image_path, str(e))

def process_images(folder_path, task_prompt, caption_type="EN", additional_tags=""):
    error_folder = os.path.join(folder_path, "error_img")
    os.makedirs(error_folder, exist_ok=True)
    
    total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
    
    processed_count = 0
    with tqdm(total=total_files, desc="Processing Images") as pbar:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    image_path = os.path.join(root, file)
                    process_single_image(image_path, task_prompt, caption_type, additional_tags)
                    processed_count += 1
                    print(f"{processed_count}/{total_files}") 
                    pbar.update(1)

def main():
    if len(sys.argv) != 5:
        print("Usage: python gen_caption.py <folder_path> <task_prompt> <caption_type> <additional_tags>")
        sys.exit(1)

    folder_path = sys.argv[1]
    task_prompt = sys.argv[2]
    caption_type = sys.argv[3]
    additional_tags = sys.argv[4]

    process_images(folder_path, task_prompt, caption_type, additional_tags)

if __name__ == "__main__":
    main()