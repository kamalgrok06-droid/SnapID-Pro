import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os, threading, cv2


# ================= SPLASH ================= #
def show_splash(root):
    splash = tb.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x250+500+300")

    try:
        img = Image.open("assets/logo.png").resize((200, 80))
        logo = ImageTk.PhotoImage(img)
        lbl = tb.Label(splash, image=logo)
        lbl.image = logo
        lbl.pack(expand=True)
    except:
        tb.Label(splash, text="SnapID Pro", font=("Segoe UI", 20)).pack(expand=True)

    splash.update()
    splash.after(2000, splash.destroy)


# ================= MAIN APP ================= #
class SnapIDPro:

    def __init__(self, root):
        self.root = root
        self.root.title("SnapID Pro")
        self.root.geometry("1100x720")

        try:
            self.root.iconbitmap("assets/snapid_pro_icon.ico")
        except:
            pass

        self.mode = "text"
        self.image_files = []
        self.output_folder = ""
        self.processed_images = []

        self.build_ui()

    # ================= UI ================= #
    def build_ui(self):

        # HEADER
        header = tb.Frame(self.root)
        header.pack(fill=X, pady=10)

        try:
            logo = Image.open("assets/logo.png").resize((160, 50))
            self.logo = ImageTk.PhotoImage(logo)
            tb.Label(header, image=self.logo).pack(side=LEFT, padx=10)
        except:
            tb.Label(header, text="SnapID Pro", font=("Segoe UI", 20, "bold")).pack(side=LEFT)

        # Dark Mode Toggle
        tb.Button(header, text="🌙 Toggle Mode",
                  command=self.toggle_theme).pack(side=RIGHT, padx=10)

        # Drag & Drop
        drop_label = tb.Label(self.root, text="Drag & Drop Images Here", bootstyle="info")
        drop_label.pack(pady=5, fill=X)

        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind("<<Drop>>", self.drop_files)

        # MODE BUTTONS
        btn_frame = tb.Frame(self.root)
        btn_frame.pack(fill=X, pady=10)

        tb.Button(btn_frame, text="Add Text Only", bootstyle="primary",
                  command=lambda: self.set_mode("text")).pack(side=LEFT, padx=10)

        tb.Button(btn_frame, text="Passport Crop", bootstyle="success",
                  command=lambda: self.set_mode("crop")).pack(side=LEFT, padx=10)

        tb.Button(btn_frame, text="Crop + Text", bootstyle="warning",
                  command=lambda: self.set_mode("crop+text")).pack(side=LEFT, padx=10)

        # BODY
        body = tb.Frame(self.root)
        body.pack(fill=BOTH, expand=True, padx=10)

        left = tb.Frame(body)
        left.pack(side=LEFT, fill=Y, padx=10)

        right = tb.Frame(body)
        right.pack(side=RIGHT, fill=BOTH, expand=True)

        # INPUT
        tb.Button(left, text="Select Input Folder", bootstyle="secondary",
                  command=self.select_input_folder).pack(pady=10, fill=X)

        self.output_var = tb.StringVar()
        tb.Entry(left, textvariable=self.output_var).pack(fill=X, pady=5)

        tb.Button(left, text="Browse Output", bootstyle="secondary",
                  command=self.select_output).pack(pady=5, fill=X)

        tb.Button(left, text="Process Images", bootstyle="success",
                  command=self.start_processing).pack(pady=20, fill=X)

        self.save_btn = tb.Button(left, text="Save All Images", bootstyle="primary",
                                 state=DISABLED, command=self.save_all)
        self.save_btn.pack(fill=X)

        # PREVIEW
        self.preview_frame = tb.Frame(right)
        self.preview_frame.pack(fill=BOTH, expand=True)

        # FOOTER
        tb.Label(self.root, text="© 2026 Kamal | SnapID Pro",
                 font=("Segoe UI", 9)).pack(pady=5)

    def set_mode(self, m):
        self.mode = m

    def toggle_theme(self):
        current = self.root.style.theme.name
        if current == "flatly":
            self.root.style.theme_use("darkly")
        else:
            self.root.style.theme_use("flatly")

    # ================= DRAG DROP ================= #
    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self.image_files.extend(files)
        messagebox.showinfo("Loaded", f"{len(files)} images added")

    # ================= FILE SELECT ================= #
    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_files = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".png", ".jpeg"))
            ]
            messagebox.showinfo("Loaded", f"{len(self.image_files)} images loaded")

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.output_var.set(folder)

    # ================= FACE CROP ================= #
    def detect_and_crop_face(self, path):
        img_cv = cv2.imread(path)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            return None

        x, y, w, h = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)[0]

        top = max(0, int(y - h * 1.5))
        bottom = min(img_cv.shape[0], int(y + h * 2))
        left = max(0, int(x - w * 0.5))
        right = min(img_cv.shape[1], int(x + w * 1.5))

        crop = img_cv[top:bottom, left:right]
        crop = cv2.resize(crop, (413, 531))

        return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

    # ================= TEXT ================= #
    def add_text(self, img, path):
        draw = ImageDraw.Draw(img, "RGBA")

        text = os.path.splitext(os.path.basename(path))[0]

        font_size = int(min(img.width, img.height) * 0.05)
        font = self.get_font(font_size)

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        margin = int(min(img.width, img.height) * 0.03)

        x = img.width - tw - margin
        y = img.height - th - margin

        draw.rectangle([x-8, y-4, x+tw+8, y+th+4], fill=(255,255,255,230))
        draw.text((x, y), text, fill=(0,0,0), font=font)

        return img

    def get_font(self, size):
        try:
            return ImageFont.truetype("Aptos.ttf", size)
        except:
            return ImageFont.load_default()

    # ================= PROCESS ================= #
    def process_images(self):
        self.processed_images.clear()

        for path in self.image_files:

            if self.mode == "text":
                img = Image.open(path).convert("RGBA")

            elif self.mode == "crop":
                img = self.detect_and_crop_face(path)
                if img is None:
                    continue

            elif self.mode == "crop+text":
                img = self.detect_and_crop_face(path)
                if img is None:
                    continue

            if "text" in self.mode:
                img = self.add_text(img, path)

            self.processed_images.append((img.copy(), path))

        self.show_preview()

    def show_preview(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()

        for i, (img, _) in enumerate(self.processed_images):
            preview = img.resize((120, 120))
            tk_img = ImageTk.PhotoImage(preview)

            lbl = tb.Label(self.preview_frame, image=tk_img)
            lbl.image = tk_img
            lbl.grid(row=i//4, column=i % 4, padx=10, pady=10)

        self.save_btn.config(state=NORMAL)

    # ================= SAVE ================= #
    def save_all(self):
        for img, path in self.processed_images:
            name = os.path.basename(path)
            out = os.path.join(self.output_folder, name)

            ext = os.path.splitext(path)[1].lower()

            if ext in [".jpg", ".jpeg"]:
                img.convert("RGB").save(out, "JPEG", quality=95, subsampling=0)
            else:
                img.save(out)

        messagebox.showinfo("Saved", "All images saved successfully")

    def start_processing(self):
        if not self.image_files or not self.output_folder:
            messagebox.showerror("Error", "Select folders first")
            return

        threading.Thread(target=self.process_images, daemon=True).start()


# ================= RUN ================= #
if __name__ == "__main__":
    app = TkinterDnD.Tk()
    tb.Style("flatly")

    show_splash(app)
    app.after(2000, lambda: SnapIDPro(app))

    app.mainloop()
