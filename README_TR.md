# 🛠️ Litematica to Schematic Converter (Türkçe Dokümantasyon)

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Minecraft Version](https://img.shields.io/badge/minecraft-1.13%2B-orange.svg)
![WorldEdit Format](https://img.shields.io/badge/format-Sponge%20V2%20(.schem)-brightgreen.svg)

> Bu dokümanı başka bir dilde okuyun:  
> 🇺🇸 **[English](README.md)**

Minecraft **Litematica** (`.litematic`) yapı dosyalarını doğrudan modern **WorldEdit / FastAsyncWorldEdit (FAWE)** uyumlu **Sponge V2** (`.schem`) formatına dönüştüren hızlı, güvenilir ve tam uyumlu bir Python CLI aracıdır.

---

## 🎯 Projenin Amacı

Minecraft'ta Fabric/Quilt tabanlı **Litematica** modu tarafından kullanılan `.litematic` formatındaki yapı şablonları, Forge/Paper/Spigot sunucularında çalışan **WorldEdit** veya **FAWE** eklentileriyle doğrudan yüklenemez. 

Bu araç, herhangi bir ek Minecraft istemcisi açmaya gerek kalmadan Litematica dosyalarını doğrudan NBT seviyesinde işleyerek tam uyumlu `.schem` dosyalarına dönüştürmenizi sağlar.

---

## 🧱 Minecraft Sürüm Uyumluluğu

Bu araç **Minecraft 1.13 ve üzeri tüm modern sürümler** (1.16, 1.20, 26.2 vb.) ile tam uyumludur.

### Alt Sınır Neden 1.13?
Minecraft, 1.13 sürümü ile birlikte kod yapısında devasa bir değişikliğe gitti (**The Flattening / Düzleştirme**). Bu sürümden önce bloklar rakamlarla (ID) ve meta verilerle ifade ediliyordu (Örneğin kırmızı yün için `35:14` kullanılıyordu). 1.13 ile birlikte tüm bloklar metin formatına (Örn: `minecraft:red_wool`) geçirildi. Geliştirdiğimiz betik, modern **Sponge V2** standartlarını kullanarak metin tabanlı bir palet oluşturduğu için 1.12.2 ve önceki sürümlerdeki rakamsal sistemi desteklemez.

### Üst Sınır Neden Yok (Geleceğe Uyumlu / Future-Proof)?
Python betiğini yazarken blok isimlerini koda sabit kodlama (hardcode) yöntemiyle elle girmedik. Betik, Litematica dosyasını okurken karşısına çıkan tüm blok kimliklerini (`block.id` ve `block.properties`) o an **dinamik olarak algılayıp** yeni palete kopyalar. Dolayısıyla oyuna 26.2 veya daha sonraki bir sürümde yepyeni bir blok eklendiğinde bile, betik bu bloğun ismini bozmadan doğrudan NBT (Named Binary Tag) yapısına yazar ve WorldEdit'in tanımasını sağlar.

---

## ✨ Öne Çıkan Özellikler

- 📦 **Sponge V2 NBT Standardı Tam Desteği**: WorldEdit v7+ ve FAWE standartlarına tam uyumlu NBT veri ağacı yapısı (`Version: 2`, `DataVersion: 2586`).
- 🔢 **LEB128 VarInt Bayt Kodlaması**: Blok indeksleri Sponge V2 standartlarının gerektirdiği şekilde dinamik VarInt (LEB128) formatında bayt dizisine dönüştürülür.
- 📐 **Otomatik Negatif Koordinat Düzeltmesi**: Litematica seçimlerinde negatif eksen yönlü kaydedilmiş bölgeler otomatik olarak sıralanır ve WorldEdit eksen düzenine (`(Y * Uzunluk + Z) * Genişlik + X`) hizalanır.
- 🎨 **Gelişmiş Blok Durum (BlockState) & Palet Yönetimi**: Blokların `minecraft:` ön ekleri, merdiven, yön, su/cam durumları ve tüm blok özellikleri eksiksiz olarak korunur ve paletlenir.
- ⚡ **Hızlı ve Kolay Kullanım**: Hem gelişmiş kullanıcılar için komut satırı (CLI) arayüzü hem de tek tıkla çalıştırma sunan Windows Toplu İş Dosyası (`start.bat`) desteği.

---

## 📥 Kurulum

Dönüştürücüyü kullanabilmek için bilgisayarınızda **Python 3.8+** yüklü olmalıdır.

1. Depoyu klonlayın veya indirin:
   ```bash
   git clone https://github.com/Ohualtex/Litematic-to-Schematic.git
   cd Litematic-to-Schematic
   ```

2. Gerekli Python kütüphanelerini yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Kullanım

Dönüştürücüyü iki farklı şekilde çalıştırabilirsiniz:

### 1. Komut Satırı (CLI) Üzerinden Kullanım

Temel dönüştürme (Çıktı dosyası girdi dosyasıyla aynı isimde `.schem` olarak oluşturulur):
```bash
python convert.py ornek_yapi.litematic
```

Özel çıktı dosyası adı belirterek dönüştürme:
```bash
python convert.py ornek_yapi.litematic -o benim_yapim.schem
```

Yardım menüsünü görüntüleme:
```bash
python convert.py --help
```

---

### 2. Windows Toplu İş Betiği (`start.bat`) Üzerinden Kullanım

Komut satırı kullanmak istemiyorsanız, Windows ortamında `start.bat` dosyasını çift tıklatarak çalıştırabilirsiniz.

1. `start.bat` dosyasını çalıştırın.
2. Açılan pencerede dönüştürmek istediğiniz dosyanın adını girin (Örn: `ev.litematic`).
3. Dönüştürme tamamlandığında aynı klasörde `.schem` dosyanız hazır olacaktır.

---

## 📁 Proje Yapısı

```text
Litematic-to-Schematic/
├── .gitignore          # Git tarafından yoksayılacak dosyalar
├── LICENSE             # MIT Lisans belgesi
├── README.md           # İngilizce Benioku dokümanı (varsayılan)
├── README_TR.md        # Türkçe Benioku dokümanı
├── requirements.txt    # Proje bağımlılıkları (litemapy, nbtlib)
├── convert.py          # Litematica -> Schematic dönüştürücü ana Python kodu
└── start.bat           # Windows kolay başlatıcı betiği
```

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Dilediğiniz gibi kullanabilir, değiştirebilir ve dağıtabilirsiniz.

---

## 👤 Yazar

**Ohualtex**
- GitHub: [@Ohualtex](https://github.com/Ohualtex)
