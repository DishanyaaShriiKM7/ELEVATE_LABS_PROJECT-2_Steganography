"""
Advanced Steganography Tool - Hide encrypted text/multiple files inside images
Features: LSB encoding, AES encryption, drag-and-drop, capacity calculator, multi-file support
Author: Cybersecurity Internship Project
"""

from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import hashlib
import json
import zipfile
from io import BytesIO


class SteganographyTool:
    """Core steganography logic with encryption and multi-file support"""
    
    def __init__(self):
        self.delimiter = "<=END=>"
        self.file_marker = "<=FILE=>"
        self.multi_file_marker = "<=MULTIFILE=>"
    
    def generate_key(self, password):
        """Generate 256-bit AES key from password"""
        return hashlib.sha256(password.encode()).digest()
    
    def encrypt_data(self, data, password):
        """Encrypt data using AES-256"""
        if not password:
            return data
        
        key = self.generate_key(password)
        iv = os.urandom(16)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad data to block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode() if isinstance(data, str) else data) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + encrypted data as base64
        return base64.b64encode(iv + encrypted).decode()
    
    def decrypt_data(self, encrypted_data, password):
        """Decrypt data using AES-256"""
        if not password:
            return encrypted_data
        
        try:
            key = self.generate_key(password)
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad data
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data.decode()
        except Exception as e:
            return None
    
    def text_to_binary(self, text):
        """Convert text to binary string"""
        binary = ''.join(format(ord(char), '08b') for char in text)
        return binary
    
    def binary_to_text(self, binary):
        """Convert binary string back to text"""
        text = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            if len(byte) == 8:
                text += chr(int(byte, 2))
        return text
    
    def calculate_capacity(self, image_path):
        """Calculate how many bytes can be hidden in image"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            # 3 bits per pixel (RGB), divided by 8 for bytes
            max_bytes = (width * height * 3) // 8
            # Reserve space for delimiter
            usable_bytes = max_bytes - len(self.delimiter) - 100
            return usable_bytes
        except:
            return 0
    
    def create_zip_from_files(self, file_paths):
        """Create a ZIP archive from multiple files in memory"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                zip_file.write(file_path, filename)
        
        return zip_buffer.getvalue()
    
    def encode_multiple_files(self, image_path, file_paths, output_path, password=None):
        """Hide multiple files inside image as a ZIP archive"""
        try:
            # Create ZIP archive
            zip_data = self.create_zip_from_files(file_paths)
            
            # Create metadata
            file_list = [os.path.basename(f) for f in file_paths]
            metadata = {
                'type': 'multifile',
                'count': len(file_paths),
                'files': file_list,
                'total_size': len(zip_data)
            }
            
            # Encode ZIP data as base64
            zip_b64 = base64.b64encode(zip_data).decode()
            
            # Combine metadata and ZIP
            payload = json.dumps(metadata) + self.multi_file_marker + zip_b64
            
            # Encrypt if password provided
            if password:
                payload = self.encrypt_data(payload, password)
            
            # Use text encoding method
            return self.encode_image(image_path, payload, output_path)
            
        except Exception as e:
            return False, f"Error encoding files: {str(e)}"
    
    def encode_file(self, image_path, file_path, output_path, password=None):
        """Hide single file inside image"""
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Create metadata
            filename = os.path.basename(file_path)
            metadata = {
                'type': 'file',
                'name': filename,
                'size': len(file_data)
            }
            
            # Encode file data as base64
            file_b64 = base64.b64encode(file_data).decode()
            
            # Combine metadata and file
            payload = json.dumps(metadata) + self.file_marker + file_b64
            
            # Encrypt if password provided
            if password:
                payload = self.encrypt_data(payload, password)
            
            # Use text encoding method
            return self.encode_image(image_path, payload, output_path)
            
        except Exception as e:
            return False, f"Error encoding file: {str(e)}"
    
    def decode_files(self, image_path, output_dir, password=None):
        """Extract hidden file(s) from image - handles both single and multiple files"""
        try:
            # Decode data
            success, data = self.decode_image(image_path, password)
            if not success:
                return False, data
            
            # Check if it's multiple files
            if self.multi_file_marker in data:
                parts = data.split(self.multi_file_marker)
                metadata = json.loads(parts[0])
                zip_b64 = parts[1]
                
                # Decode ZIP
                zip_data = base64.b64decode(zip_b64.encode())
                
                # Extract files from ZIP
                zip_buffer = BytesIO(zip_data)
                extracted_files = []
                
                with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                    for file_info in zip_file.namelist():
                        zip_file.extract(file_info, output_dir)
                        extracted_files.append(file_info)
                
                return True, f"Extracted {len(extracted_files)} files:\n" + "\n".join(extracted_files)
            
            # Check if it's a single file
            elif self.file_marker in data:
                parts = data.split(self.file_marker)
                metadata = json.loads(parts[0])
                file_b64 = parts[1]
                
                # Decode file
                file_data = base64.b64decode(file_b64.encode())
                
                # Save file
                output_path = os.path.join(output_dir, metadata['name'])
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                
                return True, f"File extracted: {output_path}"
            
            else:
                return False, "No file found in image (text message only)"
            
        except Exception as e:
            return False, f"Error decoding: {str(e)}"
    
    def encode_image(self, image_path, secret_message, output_path, password=None):
        """Hide secret message in image using LSB technique with optional encryption"""
        try:
            img = Image.open(image_path)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Encrypt message if password provided
            if password:
                secret_message = self.encrypt_data(secret_message, password)
            
            secret_message += self.delimiter
            binary_message = self.text_to_binary(secret_message)
            message_length = len(binary_message)
            
            width, height = img.size
            max_bytes = width * height * 3
            
            if message_length > max_bytes:
                return False, "Data too large for this image!"
            
            data_index = 0
            encoded_img = img.copy()
            pixels = encoded_img.load()
            
            for y in range(height):
                for x in range(width):
                    if data_index < message_length:
                        pixel = list(pixels[x, y])
                        
                        for color_channel in range(3):
                            if data_index < message_length:
                                pixel[color_channel] = (pixel[color_channel] & 0xFE) | int(binary_message[data_index])
                                data_index += 1
                        
                        pixels[x, y] = tuple(pixel)
                    else:
                        break
                if data_index >= message_length:
                    break
            
            encoded_img.save(output_path, 'PNG')
            return True, "Data hidden successfully!"
            
        except Exception as e:
            return False, f"Error encoding: {str(e)}"
    
    def decode_image(self, image_path, password=None):
        """Extract hidden message from image with optional decryption"""
        try:
            img = Image.open(image_path)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            pixels = img.load()
            
            binary_message = ""
            
            for y in range(height):
                for x in range(width):
                    pixel = pixels[x, y]
                    
                    for color_channel in range(3):
                        binary_message += str(pixel[color_channel] & 1)
            
            extracted_text = self.binary_to_text(binary_message)
            
            if self.delimiter in extracted_text:
                actual_message = extracted_text.split(self.delimiter)[0]
                
                # Decrypt if password provided
                if password:
                    decrypted = self.decrypt_data(actual_message, password)
                    if decrypted is None:
                        return False, "Wrong password or corrupted data!"
                    actual_message = decrypted
                
                return True, actual_message
            else:
                return False, "No hidden data found!"
                
        except Exception as e:
            return False, f"Error decoding: {str(e)}"


class SteganographyGUI:
    """Advanced GUI with multi-file support"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Steganography Tool - Multi-File Support")
        self.root.geometry("850x750")
        self.root.resizable(False, False)
        
        self.steg_tool = SteganographyTool()
        self.image_path = None
        self.file_paths = []  # List for multiple files
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create GUI components"""
        
        # Title
        title_label = tk.Label(
            self.root, 
            text="🔒 Advanced Steganography Tool", 
            font=("Arial", 20, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            self.root,
            text="Hide Multiple Files + Encryption + Drag & Drop",
            font=("Arial", 10),
            fg="#7f8c8d"
        )
        subtitle_label.pack()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Encode Tab
        self.encode_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.encode_frame, text='  🔐 Encode (Hide)  ')
        self.create_encode_tab()
        
        # Decode Tab
        self.decode_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.decode_frame, text='  🔓 Decode (Extract)  ')
        self.create_decode_tab()
        
        # Status bar
        self.status_label = tk.Label(
            self.root, 
            text="Ready | Drag & drop images/files directly!", 
            relief=tk.SUNKEN, 
            anchor='w',
            bg='#34495e',
            fg='white',
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_encode_tab(self):
        """Create encode tab with multi-file support"""
        
        # Drag-drop area for image
        drop_frame = tk.Frame(
            self.encode_frame,
            bg='#3498db',
            height=80
        )
        drop_frame.pack(fill='x', padx=20, pady=10)
        drop_frame.pack_propagate(False)
        
        drop_label = tk.Label(
            drop_frame,
            text="📁 Drag & Drop Cover Image Here",
            font=("Arial", 12, "bold"),
            bg='#3498db',
            fg='white'
        )
        drop_label.pack(expand=True)
        
        # Enable drag and drop
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.drop_encode_image)
        
        # Image selection
        img_frame = tk.LabelFrame(
            self.encode_frame, 
            text="1. Cover Image", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        img_frame.pack(fill='x', padx=20, pady=10)
        
        self.encode_img_label = tk.Label(
            img_frame, 
            text="No image selected", 
            bg='#ecf0f1',
            fg='#7f8c8d'
        )
        self.encode_img_label.pack(side='left')
        
        btn_frame = tk.Frame(img_frame, bg='#ecf0f1')
        btn_frame.pack(side='right')
        
        tk.Button(
            btn_frame, 
            text="Browse Image", 
            command=self.select_encode_image,
            bg='#3498db',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame, 
            text="📊 Check Capacity", 
            command=self.check_capacity,
            bg='#9b59b6',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='left')
        
        # Mode selection
        mode_frame = tk.LabelFrame(
            self.encode_frame, 
            text="2. Select Mode", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        mode_frame.pack(fill='x', padx=20, pady=10)
        
        self.encode_mode = tk.StringVar(value="text")
        
        tk.Radiobutton(
            mode_frame,
            text="📝 Hide Text Message",
            variable=self.encode_mode,
            value="text",
            command=self.toggle_encode_mode,
            bg='#ecf0f1',
            font=("Arial", 10)
        ).pack(side='left', padx=15)
        
        tk.Radiobutton(
            mode_frame,
            text="📄 Hide Single File",
            variable=self.encode_mode,
            value="file",
            command=self.toggle_encode_mode,
            bg='#ecf0f1',
            font=("Arial", 10)
        ).pack(side='left', padx=15)
        
        tk.Radiobutton(
            mode_frame,
            text="📦 Hide Multiple Files",
            variable=self.encode_mode,
            value="multifile",
            command=self.toggle_encode_mode,
            bg='#ecf0f1',
            font=("Arial", 10)
        ).pack(side='left', padx=15)
        
        # Text message input
        self.text_frame = tk.LabelFrame(
            self.encode_frame, 
            text="3. Secret Message", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        self.text_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.message_text = tk.Text(
            self.text_frame, 
            height=5, 
            font=("Consolas", 10),
            wrap='word',
            bg='white'
        )
        self.message_text.pack(fill='both', expand=True)
        
        # Single file selection
        self.file_frame = tk.LabelFrame(
            self.encode_frame, 
            text="3. Select File to Hide", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        
        self.file_label = tk.Label(
            self.file_frame,
            text="No file selected",
            bg='#ecf0f1',
            fg='#7f8c8d'
        )
        self.file_label.pack(side='left')
        
        tk.Button(
            self.file_frame,
            text="Browse File",
            command=self.select_single_file,
            bg='#e67e22',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='right')
        
        # Multiple files selection
        self.multifile_frame = tk.LabelFrame(
            self.encode_frame, 
            text="3. Select Multiple Files to Hide", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        
        # Listbox for multiple files
        list_container = tk.Frame(self.multifile_frame, bg='#ecf0f1')
        list_container.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')
        
        self.files_listbox = tk.Listbox(
            list_container,
            height=5,
            font=("Arial", 9),
            yscrollcommand=scrollbar.set,
            bg='white'
        )
        self.files_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Buttons for file management
        multifile_btn_frame = tk.Frame(self.multifile_frame, bg='#ecf0f1')
        multifile_btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(
            multifile_btn_frame,
            text="➕ Add Files",
            command=self.add_files,
            bg='#27ae60',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='left', padx=5)
        
        tk.Button(
            multifile_btn_frame,
            text="➖ Remove Selected",
            command=self.remove_file,
            bg='#e74c3c',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='left', padx=5)
        
        tk.Button(
            multifile_btn_frame,
            text="🗑️ Clear All",
            command=self.clear_files,
            bg='#95a5a6',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='left', padx=5)
        
        self.file_count_label = tk.Label(
            multifile_btn_frame,
            text="Files: 0 | Total: 0 KB",
            bg='#ecf0f1',
            font=("Arial", 9, "bold"),
            fg='#2c3e50'
        )
        self.file_count_label.pack(side='right', padx=10)
        
        # Password (optional)
        pwd_frame = tk.LabelFrame(
            self.encode_frame, 
            text="4. Password (Optional - for encryption)", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        pwd_frame.pack(fill='x', padx=20, pady=10)
        
        self.encode_password = tk.Entry(
            pwd_frame,
            show='*',
            font=("Arial", 10),
            bg='white'
        )
        self.encode_password.pack(fill='x')
        
        # Encode button
        tk.Button(
            self.encode_frame, 
            text="🔐 HIDE DATA IN IMAGE", 
            command=self.encode_data,
            bg='#27ae60',
            fg='white',
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(pady=15)
    
    def create_decode_tab(self):
        """Create decode tab"""
        
        # Drag-drop area
        drop_frame = tk.Frame(
            self.decode_frame,
            bg='#e74c3c',
            height=100
        )
        drop_frame.pack(fill='x', padx=20, pady=10)
        drop_frame.pack_propagate(False)
        
        drop_label = tk.Label(
            drop_frame,
            text="📁 Drag & Drop Encoded Image Here\n(or use Browse button below)",
            font=("Arial", 12, "bold"),
            bg='#e74c3c',
            fg='white'
        )
        drop_label.pack(expand=True)
        
        # Enable drag and drop
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.drop_decode_image)
        
        # Image selection
        img_frame = tk.LabelFrame(
            self.decode_frame, 
            text="1. Encoded Image", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        img_frame.pack(fill='x', padx=20, pady=10)
        
        self.decode_img_label = tk.Label(
            img_frame, 
            text="No image selected", 
            bg='#ecf0f1',
            fg='#7f8c8d'
        )
        self.decode_img_label.pack(side='left')
        
        tk.Button(
            img_frame, 
            text="Browse Image", 
            command=self.select_decode_image,
            bg='#3498db',
            fg='white',
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side='right')
        
        # Password
        pwd_frame = tk.LabelFrame(
            self.decode_frame, 
            text="2. Password (if encrypted)", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        pwd_frame.pack(fill='x', padx=20, pady=10)
        
        self.decode_password = tk.Entry(
            pwd_frame,
            show='*',
            font=("Arial", 10),
            bg='white'
        )
        self.decode_password.pack(fill='x')
        
        # Extracted message display
        msg_frame = tk.LabelFrame(
            self.decode_frame, 
            text="3. Extracted Data", 
            font=("Arial", 11, "bold"),
            bg='#ecf0f1',
            padx=20,
            pady=10
        )
        msg_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.extracted_text = tk.Text(
            msg_frame, 
            height=8, 
            font=("Consolas", 10),
            wrap='word',
            bg='white',
            state='disabled'
        )
        self.extracted_text.pack(fill='both', expand=True)
        
        # Decode buttons
        btn_frame = tk.Frame(self.decode_frame, bg='#ecf0f1')
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame, 
            text="📝 EXTRACT TEXT", 
            command=self.decode_message,
            bg='#e74c3c',
            fg='white',
            font=("Arial", 11, "bold"),
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        tk.Button(
            btn_frame, 
            text="📄 EXTRACT FILE(S)", 
            command=self.decode_files,
            bg='#f39c12',
            fg='white',
            font=("Arial", 11, "bold"),
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=10)
    
    def drop_encode_image(self, event):
        """Handle drag and drop for encode image"""
        file_path = event.data.strip('{}')
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            self.image_path = file_path
            filename = os.path.basename(file_path)
            self.encode_img_label.config(text=filename, fg='#27ae60')
            self.status_label.config(text=f"Dropped: {filename}")
        else:
            messagebox.showerror("Error", "Please drop an image file!")
    
    def drop_decode_image(self, event):
        """Handle drag and drop for decode image"""
        file_path = event.data.strip('{}')
        if file_path.lower().endswith('.png'):
            self.decode_image_path = file_path
            filename = os.path.basename(file_path)
            self.decode_img_label.config(text=filename, fg='#27ae60')
            self.status_label.config(text=f"Dropped: {filename}")
        else:
            messagebox.showerror("Error", "Please drop a PNG file!")
    
    def toggle_encode_mode(self):
        """Toggle between text, file, and multi-file mode"""
        mode = self.encode_mode.get()
        
        # Hide all frames first
        self.text_frame.pack_forget()
        self.file_frame.pack_forget()
        self.multifile_frame.pack_forget()
        
        # Show appropriate frame
        if mode == "text":
            self.text_frame.pack(fill='both', expand=True, padx=20, pady=10)
        elif mode == "file":
            self.file_frame.pack(fill='x', padx=20, pady=10)
        else:  # multifile
            self.multifile_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    def select_encode_image(self):
        """Select image for encoding"""
        filepath = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if filepath:
            self.image_path = filepath
            filename = os.path.basename(filepath)
            self.encode_img_label.config(text=filename, fg='#27ae60')
            self.status_label.config(text=f"Selected: {filename}")
    
    def select_single_file(self):
        """Select single file to hide"""
        filepath = filedialog.askopenfilename(
            title="Select File to Hide",
            filetypes=[("All files", "*.*")]
        )
        if filepath:
            self.single_file_path = filepath
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            self.file_label.config(
                text=f"{filename} ({file_size} bytes)", 
                fg='#27ae60'
            )
    
    def add_files(self):
        """Add multiple files to hide"""
        filepaths = filedialog.askopenfilenames(
            title="Select Files to Hide",
            filetypes=[("All files", "*.*")]
        )
        
        for filepath in filepaths:
            if filepath not in self.file_paths:
                self.file_paths.append(filepath)
                filename = os.path.basename(filepath)
                file_size = os.path.getsize(filepath)
                self.files_listbox.insert(tk.END, f"{filename} ({file_size} bytes)")
        
        self.update_file_count()
    
    def remove_file(self):
        """Remove selected file from list"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            self.files_listbox.delete(index)
            self.file_paths.pop(index)
            self.update_file_count()
    
    def clear_files(self):
        """Clear all files from list"""
        self.files_listbox.delete(0, tk.END)
        self.file_paths = []
        self.update_file_count()
    
    def update_file_count(self):
        """Update file count and total size display"""
        total_size = sum(os.path.getsize(f) for f in self.file_paths)
        total_kb = total_size / 1024
        self.file_count_label.config(
            text=f"Files: {len(self.file_paths)} | Total: {total_kb:.2f} KB"
        )
    
    def check_capacity(self):
        """Check how much data can be hidden"""
        if not self.image_path:
            messagebox.showerror("Error", "Please select an image first!")
            return
        
        capacity = self.steg_tool.calculate_capacity(self.image_path)
        capacity_kb = capacity / 1024
        capacity_mb = capacity / 1024 / 1024
        
        messagebox.showinfo(
            "Image Capacity",
            f"This image can hide approximately:\n\n"
            f"• {capacity:,} bytes\n"
            f"• {capacity_kb:.2f} KB\n"
            f"• {capacity_mb:.2f} MB\n\n"
            f"Note: Actual capacity may be less due to encryption overhead."
        )
    
    def select_decode_image(self):
        """Select image for decoding"""
        filepath = filedialog.askopenfilename(
            title="Select Encoded Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filepath:
            self.decode_image_path = filepath
            filename = os.path.basename(filepath)
            self.decode_img_label.config(text=filename, fg='#27ae60')
            self.status_label.config(text=f"Selected: {filename}")
    
    def encode_data(self):
        """Encode message or file(s) into image"""
        if not self.image_path:
            messagebox.showerror("Error", "Please select a cover image first!")
            return
        
        password = self.encode_password.get() or None
        mode = self.encode_mode.get()
        
        if mode == "text":
            message = self.message_text.get("1.0", tk.END).strip()
            if not message:
                messagebox.showerror("Error", "Please enter a message to hide!")
                return
            
            output_path = filedialog.asksaveasfilename(
                title="Save Encoded Image As",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            
            if not output_path:
                return
            
            self.status_label.config(text="Encoding message...")
            self.root.update()
            
            success, result_msg = self.steg_tool.encode_image(
                self.image_path, 
                message, 
                output_path,
                password
            )
            
        elif mode == "file":
            if not hasattr(self, 'single_file_path'):
                messagebox.showerror("Error", "Please select a file to hide!")
                return
            
            output_path = filedialog.asksaveasfilename(
                title="Save Encoded Image As",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            
            if not output_path:
                return
            
            self.status_label.config(text="Encoding file...")
            self.root.update()
            
            success, result_msg = self.steg_tool.encode_file(
                self.image_path,
                self.single_file_path,
                output_path,
                password
            )
            
        else:  # multifile
            if not self.file_paths:
                messagebox.showerror("Error", "Please add files to hide!")
                return
            
            output_path = filedialog.asksaveasfilename(
                title="Save Encoded Image As",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            
            if not output_path:
                return
            
            self.status_label.config(text=f"Encoding {len(self.file_paths)} files...")
            self.root.update()
            
            success, result_msg = self.steg_tool.encode_multiple_files(
                self.image_path,
                self.file_paths,
                output_path,
                password
            )
        
        if success:
            enc_msg = " (Encrypted)" if password else ""
            messagebox.showinfo("Success", f"{result_msg}{enc_msg}\n\nSaved to: {output_path}")
            self.status_label.config(text="Encoding successful!")
        else:
            messagebox.showerror("Error", result_msg)
            self.status_label.config(text="Encoding failed!")
    
    def decode_message(self):
        """Decode text message from image"""
        if not hasattr(self, 'decode_image_path') or not self.decode_image_path:
            messagebox.showerror("Error", "Please select an encoded image first!")
            return
        
        password = self.decode_password.get() or None
        
        self.status_label.config(text="Extracting message...")
        self.root.update()
        
        success, message = self.steg_tool.decode_image(self.decode_image_path, password)
        
        self.extracted_text.config(state='normal')
        self.extracted_text.delete("1.0", tk.END)
        
        if success:
            self.extracted_text.insert("1.0", message)
            self.status_label.config(text="Message extracted successfully!")
        else:
            self.extracted_text.insert("1.0", f"ERROR: {message}")
            self.status_label.config(text="Extraction failed!")
        
        self.extracted_text.config(state='disabled')
    
    def decode_files(self):
        """Decode file(s) from image"""
        if not hasattr(self, 'decode_image_path') or not self.decode_image_path:
            messagebox.showerror("Error", "Please select an encoded image first!")
            return
        
        output_dir = filedialog.askdirectory(title="Select folder to save extracted file(s)")
        if not output_dir:
            return
        
        password = self.decode_password.get() or None
        
        self.status_label.config(text="Extracting file(s)...")
        self.root.update()
        
        success, message = self.steg_tool.decode_files(
            self.decode_image_path,
            output_dir,
            password
        )
        
        if success:
            messagebox.showinfo("Success", message)
            self.status_label.config(text="File(s) extracted successfully!")
        else:
            messagebox.showerror("Error", message)
            self.status_label.config(text="Extraction failed!")


def main():
    """Main function with drag-and-drop support"""
    root = TkinterDnD.Tk()
    app = SteganographyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
