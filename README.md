# 🔒 Advanced Steganography Tool

---

## 🎯 What is This?

A professional steganography application that lets you secretly hide messages and files inside images. Features military-grade encryption, drag-and-drop interface, and multi-file support.

**Built for:** Cybersecurity Internship Project  
**Developer:** [Dishanyaa Shrii K M ]

---

## ✨ Key Features

- 🖼️ **LSB Steganography** - Hide data invisibly in image pixels
- 🔐 **AES-256 Encryption** - Password-protect your hidden data
- 📦 **Multi-File Support** - Hide multiple files in a single image
- 🖱️ **Drag & Drop** - User-friendly interface
- 📊 **Capacity Calculator** - Check image storage limits
- 🎨 **Format Support** - PNG, JPG, BMP input | PNG output

---

## 🚀 Quick Start

### Installation

```bash
# 1. Clone the repository

# 2. Install dependencies

# 3. Run the application

```

### Requirements

- Python 3.8+
- Libraries: `pillow`, `cryptography`, `tkinterdnd2`

---

## 📖 Usage

### Hide Text in Image
1. Select a cover image
2. Enter your secret message
3. (Optional) Add password
4. Click "Hide Data" and save

### Hide Files in Image
1. Select a cover image
2. Choose file(s) to hide
3. (Optional) Add password
4. Click "Hide Data" and save

### Extract Hidden Data
1. Select encoded image
2. Enter password (if used)
3. Click "Extract" to reveal data

---

## 🔐 Security

- **Strengths:** Invisible hiding, AES-256 encryption, no metadata leakage
- **Limitations:** Detectable by steganalysis tools, PNG-only output, password-dependent security

**Best Practices:**
- Use strong passwords (12+ characters)
- Choose large, complex images
- Always save output as PNG
- Don't upload to social media (compression destroys data)

---

## 🧪 Testing

```bash
# Run basic tests
python -c "from PIL import Image; print('✅ Pillow OK')"
python -c "from cryptography.fernet import Fernet; print('✅ Crypto OK')"

# Test the application
python steganography_tool.py
```

---

## 🎓 Learning Outcomes

This project demonstrates:
- LSB steganography implementation
- AES encryption/decryption
- GUI development with Tkinter
- File I/O and image processing
- Cybersecurity concepts

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a pull request

---

## 📄 License

This project is developed for educational purposes as part of a cybersecurity internship.

**Disclaimer:** For educational use only. Users are responsible for legal compliance in their jurisdiction.

---

## 👨‍💻 Author

**Name:** [Dishanyaa Shrii K M]  
**Internship:** Cybersecurity Domain  
**Email:** [dishanyaaofficial@gmail.com]  
**LinkedIn:** [[Your LinkedIn](https://www.linkedin.com/in/dishan2807/)]  
**GitHub:** [@yourusername](https://github.com/DishanyaaShriiKM7)

---

## ⭐ Star This Project

If you find this project useful, please give it a star! ⭐
