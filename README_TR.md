# 🛠️ Litematica to Schematic Converter (Türkçe Dokümantasyon)

![PyPI Version](https://img.shields.io/pypi/v/litematic-to-schematic.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Minecraft Version](https://img.shields.io/badge/minecraft-1.13%2B-orange.svg)
![WorldEdit Format](https://img.shields.io/badge/format-Sponge%20V2%20(.schem)-brightgreen.svg)

> Bu dokümanı başka bir dilde okuyun:  
> 🇺🇸 **[English](README.md)**

Minecraft **Litematica** (`.litematic`) yapı dosyalarını doğrudan **WorldEdit / FastAsyncWorldEdit (FAWE)** uyumlu **Sponge V2** (`.schem`) formatına dönüştüren hızlı ve güvenilir bir Python CLI aracı ve kütüphanesidir.

---

## 🎯 Projenin Amacı

Minecraft'ta Fabric/Quilt tabanlı **Litematica** modu tarafından kullanılan `.litematic` formatındaki yapı şablonları, Forge, NeoForge, Paper veya Spigot sunucularında çalışan **WorldEdit** veya **FAWE** eklentileriyle doğrudan yüklenemez.

Bu araç, herhangi bir Minecraft istemcisi açmaya gerek kalmadan Litematica dosyalarını doğrudan NBT seviyesinde işleyerek standart Sponge V2 `.schem` dosyalarına dönüştürmenizi sağlar.

---

## ✨ Öne Çıkan Özellikler

- 🧩 **Çoklu Bölge (Multi-Region) Birleştirme ve Çakışma Politikaları**: `.litematic` içindeki tüm alt bölgeleri kapsayan küresel sınırlayıcı kutuyu (bounding box) otomatik hesaplar, bölge ofsetlerini hizalar, hava bloklarının dolu blokları ezmesini engeller ve çakışma politikası sunar (`--on-overlap overwrite|keep-first|error`).
- 📦 **Sponge V2 NBT Yapısı ve Dinamik `DataVersion`**: Girdi dosyasındaki `MinecraftDataVersion` bilgisini korur (yalnızca eksikse `2586` varsayılanını kullanır) ve Sponge V2 (`Version: 2`) NBT ağacı üretir.
- 🧰 **BlockEntities & Entities Aktarımı**: Sandık, varil, shulker kutusu, tabela gibi blok varlıklarını (`BlockEntities`) ve zırh askısı, eşya çerçevesi, tablo, vagon gibi varlıkları (`Entities`) küresel koordinat hizalaması, `TileX/Y/Z` dönüşümü ve `UUID`/`Id` temizliği ile korur.
- 🔧 **Modlu ve Vanilla Namespace Koruması**: Modlu blok kimliklerini (örn. `create:brass_casing`, `ae2:controller[state=online]`) bozmadan korur; yalnızca namespace içermeyen kimliklere `minecraft:` öneki ekler.
- 🔢 **LEB128 VarInt Bayt Kodlaması**: Blok palet indekslerini işaretli 8-bit NBT `ByteArray` akışına dinamik LEB128 VarInt formatında kodlar ve `128` üstü geniş blok paletlerini sorunsuz destekler.
- 📐 **Negatif Koordinat Eksen Hizalaması**: Litematica seçimlerinde negatif eksen yönlü kaydedilmiş bölgeleri otomatik olarak sıralar ve WorldEdit eksen düzenine (`(Y * Uzunluk + Z) * Genişlik + X`) hizalar.

---

## 🧱 Minecraft Sürüm Uyumluluğu ve Kapsam

Bu araç **Minecraft 1.13+ şemalarını** (1.13'ten 1.20, 1.21+ vb. sürümlere kadar) destekler.

### Alt Sınır Neden 1.13?
Minecraft 1.13 (**"The Flattening / Düzleştirme"**) ile birlikte bloklar sayısal ID ve meta verilerden (örn. `35:14`) metin tabanlı blok durumlarına (örn. `minecraft:red_wool`) geçmiştir. Sponge V2 formatı metin tabanlı palet kullandığı için 1.12.2 ve öncesindeki sayısal ID sistemini desteklemez.

### Yeni Sürümler ve Modlu Bloklar Nasıl Çalışır?
Blok kimlikleri ve özellikleri (`block.id` ve `block.properties`), girdi dosyasındaki `MinecraftDataVersion` etiketiyle birlikte çalışma anında dinamik olarak okunur; koda sabitlenmiş bir blok listesi bulunmaz.

### Bilinen Format Sınırlamaları
- **Sürümler Arası Blok ID Dönüşümü Yapılmaz**: Dönüştürücü, girdi şemasının `DataVersion` değerini ve blok isimlerini olduğu gibi korur. Örneğin 1.21'e ait yeni bir bloğu içeren şemayı 1.16 sunucusuna yüklemek, o bloğu eski sürüme otomatik uyarlamaz.
- **Zamanlanmış Tickler (`PendingTicks`)**: Litematica'daki `PendingBlockTicks` ve `PendingFluidTicks` verilerinin WorldEdit Sponge V2 okuyucusunda karşılığı olmadığından, bu veriler bulunduğunda konsolda bilgilendirme mesajı verilerek atlanır.
- **Boyut Sınırları**: Sponge V2 formatında `Width`, `Height` ve `Length` alanları 16-bit işaretli `Short` tipinde tutulduğu için birleşik şema boyutu her eksende en fazla `32.767` blok olabilir.

---

## 📥 Kurulum

Bilgisayarınızda **Python 3.8+** yüklü olmalıdır.

### Seçenek 1: PyPI Üzerinden Kurulum (Önerilen)
```bash
pip install litematic-to-schematic
```
*(Bu işlem `lithetic`, `litematic-to-schematic`, `litematic2schem` ve `litematic2schematic` terminal komutlarını otomatik olarak tanımlar.)*

### Seçenek 2: Kaynak Koddan Kurulum
```bash
git clone https://github.com/Ohualtex/litematic-to-schematic.git
cd litematic-to-schematic
pip install .
```

---

## 🚀 Kullanım

### 1. Komut Satırı (CLI) Üzerinden Kullanım

Kısa `lithetic` komutuyla (veya `litematic-to-schematic` / `litematic2schem` / `python convert.py` ile):
```bash
lithetic ornek_yapi.litematic
```

Özel çıktı dosyası adı ve çoklu bölge çakışma politikası belirterek:
```bash
lithetic ornek_yapi.litematic -o benim_yapim.schem --on-overlap keep-first
```

Yardım menüsünü görüntüleme:
```bash
lithetic --help
```

### 2. Windows Toplu İş Betiği (`start.bat`) Üzerinden Kullanım

1. `start.bat` dosyasını çift tıklatarak çalıştırın.
2. Açılan pencerede dönüştürmek istediğiniz dosyanın adını girin (örn. `ev.litematic`).
3. Dönüştürme tamamlandığında aynı klasörde `.schem` dosyanız hazır olacaktır.

### 3. Test Paketini Çalıştırma

```bash
python -m unittest discover -s tests -v
```

---

## 📁 Proje Yapısı

```text
litematic-to-schematic/
├── pyproject.toml                  # PEP 621 paket yapılandırması ve CLI giriş noktaları
├── requirements.txt                # Çalışma zamanı bağımlılıkları (litemapy, nbtlib)
├── convert.py                      # Geriye dönük uyumluluk köprüsü (wrapper)
├── start.bat                       # Windows kolay başlatıcı betiği
├── README.md                       # İngilizce dokümantasyon (varsayılan)
├── README_TR.md                    # Türkçe dokümantasyon
├── LICENSE                         # MIT Lisans belgesi
├── src/
│   └── litematic_to_schematic/
│       ├── __init__.py             # Paket sürümü ve dışa aktarılan API fonksiyonları
│       ├── __main__.py             # `python -m litematic_to_schematic` giriş noktası
│       ├── converter.py            # Çekirdek Litematica -> Sponge V2 dönüşüm motoru
│       └── cli.py                  # Argparse komut satırı arayüzü
└── tests/
    └── test_converter.py           # Birim ve entegrasyon test matrisi (T01-T14)
```

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

## 👤 Yazar

**Ohualtex**
- GitHub: [@Ohualtex](https://github.com/Ohualtex)
