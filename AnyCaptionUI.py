import dearpygui.dearpygui as dpg
import threading
import subprocess
import os
import sys
import time

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

font_path = "assets/SourceHanSansCN-Regular.otf" 
image_path = "assets/1.png" 

language_mapping = {
    "English": "en_XX",
    "中文": "zh_CN",
    "日本語": "ja_XX",
    "韩文": "ko_KR",  
    "Russian": "ru_RU",
    "French ": "fr_XX",
    "Deutsch": "de_DE",
    "Español": "es_XX",
    "Eesti": "et_EE",
    "Suomi": "fi_FI",
    "阿拉伯语": "ar_AR",
    "Français": "fr_XX",
    "Italiano": "it_IT",
    "Nederlands": "nl_XX",
    "Română": "ro_RO",
    "Türkçe": "tr_TR",
    "Afrikaans": "af_ZA",
    "Hrvatski": "hr_HR",
    "Bahasa Indonesia": "id_ID",
    "Polski": "pl_PL",
    "Português": "pt_XX",
    "Svenska": "sv_SE",
    "Kiswahili": "sw_KE",
    "Xhosa": "xh_ZA",
    "Galego": "gl_ES",
    "Slovenščina": "sl_SI"
}

def load_fonts():
    with dpg.font_registry():
        with dpg.font(font_path, 22, tag="custom_font") as custom_font: 
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
            dpg.bind_font(custom_font)

def load_image():
    global scaled_height  
    width, height, channels, data = dpg.load_image(image_path)
    aspect_ratio = width / height
    target_width = 500
    scaled_height = int(target_width / aspect_ratio) 

    with dpg.texture_registry():
        dpg.add_static_texture(width=width, height=height, default_value=data, tag="header_image")


def run_gen_caption(folder_path, task_prompt, caption_type, additional_tags, model_choice):
    try:
        script_name = "gen_Florence.py" if model_choice == "Florence_2_large" else "gen_MiniCPM.py"

        command = [
            "python", script_name,
            folder_path, task_prompt, caption_type, additional_tags
        ]

        if not os.path.exists(script_name):
            dpg.set_value(output_text, f"错误: {script_name} 文件未找到！")
            return

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        for line in iter(process.stdout.readline, ''):
            dpg.set_value(output_text, line.strip())
            dpg.render_dearpygui_frame() 
        process.stdout.close()
        process.wait()

        if process.returncode != 0:
            error_output = process.stderr.read().strip()
            dpg.set_value(output_text, f"生成出错: {error_output}")
        else:
            dpg.set_value(output_text, "处理完成！")

    except Exception as e:
        dpg.set_value(output_text, f"其他错误: {str(e)}")

def start_generation():
    folder_path = dpg.get_value(input_folder_path)
    task_prompt = get_task_prompt_value()
    caption_type = language_mapping[dpg.get_value(input_caption_type)]
    additional_tags = dpg.get_value(input_additional_tags)
    model_choice = dpg.get_value(input_model_choice)
    dpg.set_value(output_text, "正在生成中...")

    threading.Thread(
        target=run_gen_caption,
        args=(folder_path, task_prompt, caption_type, additional_tags, model_choice),
        daemon=True
    ).start()

def get_task_prompt_value():
    model_choice = dpg.get_value(input_model_choice)
    
    if model_choice == "Florence_2_large":
        task_prompt_mapping = {
            "丰富": "<MORE_DETAILED_CAPTION>",
            "平均": "<DETAILED_CAPTION>",
            "精简": "<CAPTION>"
        }
    else:
        task_prompt_mapping = {
            "丰富": "Provide a comprehensive and detailed description of the image content as much as possible",
            "平均": "Describe the content on the image",
            "精简": "Briefly summarize the information in the picture"
        }
    
    selected_value = dpg.get_value(input_task_prompt)
    return task_prompt_mapping[selected_value]

def set_theme():
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (35, 35, 35)) 
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (60, 60, 60))  
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 122, 204))  
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (10, 132, 255))  
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (50, 50, 50)) 
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5) 
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 5) 

    dpg.bind_theme(theme)

def create_main_window():
    global input_folder_path, input_task_prompt, input_caption_type, input_additional_tags, input_model_choice, output_text

    with dpg.window(label="AnyCaption", width=500, height=900, no_title_bar=True, no_move=True, no_resize=True):
        dpg.add_spacer(height=10)

        dpg.add_image("header_image", width=500, height=scaled_height)  # 使用全局变量 scaled_height

        dpg.add_text("图片文件夹路径:")
        input_folder_path = dpg.add_input_text(label="", default_value="./test", width=470)

        dpg.add_spacer(height=10)
        dpg.add_text("标签数量:")
        input_task_prompt = dpg.add_combo(
            label="",
            items=["丰富", "平均", "精简"],
            default_value="丰富",
            width=470
        )

        dpg.add_spacer(height=10)
        dpg.add_text("标签语言选择（26）:")
        input_caption_type = dpg.add_combo(
            label="",
            items=[
                    "English",
                    "中文",
                    "日本語",
                    "韩文",
                    "Russian",
                    "French ",
                    "Deutsch",
                    "Español",
                    "Eesti",
                    "Suomi",
                    "阿拉伯语",
                    "Français",
                    "Italiano",
                    "Nederlands",
                    "Română",
                    "Türkçe",
                    "Afrikaans",
                    "Hrvatski",
                    "Bahasa Indonesia",
                    "Polski",
                    "Português",
                    "Svenska",
                    "Kiswahili",
                    "Xhosa",
                    "Galego",
                    "Slovenščina"
                ],  
            default_value="English", 
            width=470
        )

        dpg.add_spacer(height=10)
        dpg.add_text("触发词 (可选):")
        dpg.add_text("# 多个触发词之间用逗号隔开", bullet=False, color=(150, 150, 150))
        input_additional_tags = dpg.add_input_text(label="", default_value="@ai松柏君", width=470)

        dpg.add_spacer(height=10)
        dpg.add_text("推理模型:")
        input_model_choice = dpg.add_combo(
            label="",
            items=["Florence_2_large", "MiniCPM-V-2_6"],
            default_value="Florence_2_large",
            width=470
        )

        dpg.add_spacer(height=10)
        dpg.add_button(label="开始生成", callback=start_generation, height=35)

        dpg.add_spacer(height=10)
        output_text = dpg.add_text("等待生成...", wrap=470) 

def render_loop():
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()  
        time.sleep(0.01) 

def main():
    dpg.create_context()
    load_fonts()
    load_image()
    set_theme()

    dpg.create_viewport(title='AnyCaption', width=500, height=900)
    dpg.setup_dearpygui()
    create_main_window()  
    dpg.show_viewport()

    render_loop() 

    dpg.destroy_context()

if __name__ == "__main__":
    main()