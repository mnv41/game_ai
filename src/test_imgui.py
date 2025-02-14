import glfw
from OpenGL.GL import *
import imgui
from imgui.integrations.glfw import GlfwRenderer

def main():
    # Initialise GLFW
    if not glfw.init():
        print("Could not initialize GLFW")
        return

    print("GLFW initialized successfully")

    # Crée une fenêtre GLFW
    window = glfw.create_window(800, 600, "ImGui GLFW Test", None, None)
    if not window:
        glfw.terminate()
        print("Could not create GLFW window")
        return

    print("GLFW window created successfully")

    glfw.make_context_current(window)
    glfw.swap_interval(1)  # Active VSync

    # Initialise ImGui
    imgui.create_context()
    impl = GlfwRenderer(window)
    print("ImGui context created successfully")

    # Boucle principale
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()

        # --- Fenêtre ImGui simple ---
        imgui.begin("Test Window")
        imgui.text("Hello, ImGui!")

        # Dessine un rectangle rouge
        draw_list = imgui.get_window_draw_list()
        draw_list.add_rect(
            p_min=(50, 50),
            p_max=(200, 150),
            col=imgui.get_color_u32_rgba(1, 0, 0, 1),  # Rouge
            rounding=0.0,
            flags=0,
            thickness=2
        )

        imgui.end()

        # --- Rendu OpenGL ---
        glClearColor(0.1, 0.2, 0.3, 1.0)  # Gris bleuté
        glClear(GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    print("ImGui shutdown successfully")
    glfw.terminate()
    print("GLFW terminated successfully")

if __name__ == "__main__":
    main()