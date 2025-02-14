from ultralytics import YOLO
import mss
import cv2
import numpy as np
import time
import pygetwindow as gw
import glfw
from OpenGL.GL import *
import imgui
from imgui.integrations.glfw import GlfwRenderer
import ctypes
from typing import Optional, Dict, Tuple

# --- Configuration ---
MODEL_PATH = "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
GAME_WINDOW_TITLE = "AssaultCube"
FPS_TARGET = 60

# --- Windows Constants ---
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
GWL_EXSTYLE = -20
LWA_ALPHA = 0x00000002

def make_window_transparent_click_through(hwnd):
    """Rend la fenêtre transparente aux clics en utilisant ctypes"""
    try:
        # Obtenir l'user32.dll
        user32 = ctypes.windll.user32
        
        # Obtenir le style actuel
        ex_style = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)
        
        # Ajouter nos styles
        new_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        
        # Appliquer le nouveau style
        user32.SetWindowLongA(hwnd, GWL_EXSTYLE, new_style)
        
        # Définir la transparence
        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        
        return True
    except Exception as e:
        print(f"Erreur lors de la modification de la fenêtre: {str(e)}")
        return False

def get_game_window_coords():
    """Récupère les coordonnées de la fenêtre du jeu"""
    try:
        windows = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
        if not windows:
            return None
            
        game_window = windows[0]
        if game_window.isMinimized:
            return None

        return {
            "left": max(0, game_window.left),
            "top": max(0, game_window.top),
            "width": game_window.width,
            "height": game_window.height,
            "mon": 1
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des coordonnées: {str(e)}")
        return None

def init_glfw_imgui(width: int, height: int) -> Tuple[Optional[int], Optional[GlfwRenderer]]:
    """Initialise GLFW et ImGui"""
    try:
        if not glfw.init():
            raise Exception("Impossible d'initialiser GLFW")

        # Configuration de la fenêtre GLFW
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        glfw.window_hint(glfw.FOCUSED, glfw.FALSE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.VISIBLE, glfw.TRUE)

        window = glfw.create_window(width, height, "Overlay", None, None)
        if not window:
            raise Exception("Impossible de créer la fenêtre GLFW")

        glfw.make_context_current(window)
        
        # Récupérer le HWND de la fenêtre GLFW et le rendre transparent
        hwnd = glfw.get_win32_window(window)
        if not make_window_transparent_click_through(hwnd):
            raise Exception("Impossible de configurer la transparence de la fenêtre")

        # Initialisation de ImGui
        imgui_ctx = imgui.create_context()
        imgui.set_current_context(imgui_ctx)
        impl = GlfwRenderer(window)

        # Configuration du style ImGui
        style = imgui.get_style()
        style.window_padding = (0, 0)
        style.window_border_size = 0
        
        return window, impl

    except Exception as e:
        print(f"Erreur d'initialisation: {str(e)}")
        if 'window' in locals():
            glfw.destroy_window(window)
        glfw.terminate()
        return None, None

def draw_overlay(results, width: int, height: int, impl: GlfwRenderer, model: YOLO):
    """Dessine l'overlay avec les détections"""
    try:
        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(width, height)
        flags = (imgui.WINDOW_NO_TITLE_BAR | 
                imgui.WINDOW_NO_RESIZE | 
                imgui.WINDOW_NO_MOVE | 
                imgui.WINDOW_NO_SCROLLBAR | 
                imgui.WINDOW_NO_SAVED_SETTINGS | 
                imgui.WINDOW_NO_INPUTS | 
                imgui.WINDOW_NO_BACKGROUND)
        
        imgui.begin("Overlay", flags=flags)
        draw_list = imgui.get_window_draw_list()

        for box in results.boxes:
            try:
                x1, y1, x2, y2 = [int(coord) for coord in box.xyxy[0].tolist()]
                conf = float(box.conf[0].item())
                cls = int(box.cls[0].item())
                
                if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
                    continue
                
                label = f"{model.names[cls]}: {conf:.2f}"
                
                # Couleur en fonction de la confiance
                color = imgui.get_color_u32_rgba(
                    1.0 if conf > 0.7 else 0.0,
                    1.0 if conf <= 0.7 else 0.0,
                    0.0,
                    1.0
                )

                # Rectangle de détection
                draw_list.add_rect(x1, y1, x2, y2, color, 0.0, 0, thickness=2)
                
                # Texte avec fond
                text_size = imgui.calc_text_size(label)
                draw_list.add_rect_filled(
                    int(x1), 
                    int(y1 - text_size.y - 4),
                    int(x1 + text_size.x + 4),
                    int(y1),
                    imgui.get_color_u32_rgba(0, 0, 0, 0.7)
                )
                
                draw_list.add_text(
                    int(x1 + 2),
                    int(y1 - text_size.y - 2),
                    imgui.get_color_u32_rgba(1, 1, 1, 1),
                    label
                )

            except Exception as e:
                print(f"Erreur lors du dessin d'une boîte: {str(e)}")
                continue

        imgui.end()

    except Exception as e:
        print(f"Erreur lors du dessin de l'overlay: {str(e)}")

def main():
    """Fonction principale"""
    try:
        # Initialisation
        model = YOLO(MODEL_PATH)
        sct = mss.mss()

        print("En attente de la fenêtre du jeu...")
        while True:
            window_coords = get_game_window_coords()
            if window_coords:
                break
            time.sleep(1)

        width, height = window_coords['width'], window_coords['height']
        window, impl = init_glfw_imgui(width, height)
        if not window or not impl:
            return

        print("Overlay initialisé avec succès!")
        last_time = time.time()
        
        while not glfw.window_should_close(window):
            current_time = time.time()
            if current_time - last_time < 1.0/FPS_TARGET:
                time.sleep(1.0/FPS_TARGET - (current_time - last_time))
                continue
            
            last_time = current_time
            
            # Mise à jour de la position
            window_coords = get_game_window_coords()
            if not window_coords:
                continue

            if (width, height) != (window_coords['width'], window_coords['height']):
                width, height = window_coords['width'], window_coords['height']
                glfw.set_window_size(window, width, height)

            glfw.set_window_pos(window, window_coords['left'], window_coords['top'])
            
            try:
                # Capture et détection
                screen = sct.grab(window_coords)
                img = np.array(screen)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                results = model(img, conf=CONFIDENCE_THRESHOLD, iou=NMS_THRESHOLD, verbose=False)[0]

                # Rendu
                glfw.poll_events()
                impl.process_inputs()
                
                imgui.new_frame()
                draw_overlay(results, width, height, impl, model)
                imgui.render()

                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
                impl.render(imgui.get_draw_data())
                
                glfw.swap_buffers(window)

            except Exception as e:
                print(f"Erreur dans la boucle principale: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"Erreur fatale: {str(e)}")
    finally:
        print("\nNettoyage des ressources...")
        if 'impl' in locals():
            impl.shutdown()
        if 'window' in locals():
            glfw.destroy_window(window)
        glfw.terminate()
        if 'sct' in locals():
            sct.close()

if __name__ == "__main__":
    main()