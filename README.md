# 🎓 NeoBioAI — Yapay Zeka Tabanlı İlaç Keşif Platformu

NeoBioAI, biyoinformatik analiz ve derin öğrenme (Deep Learning) kullanarak **bir molekülün belirli bir proteine ne kadar güçlü bağlanacağını** tahmin eden uçtan uca (full-stack) bir tez projesidir. 

**Basitçe ifade etmek gerekirse:**
Yeni bir ilaç tasarladığınızı düşünün. Bu ilacın vücutta çalışıp çalışmayacağını anlamak için laboratuvarda aylarca test yapmak yerine, NeoBioAI'a molekülün kimyasal formülünü (SMILES) veriyorsunuz. Yapay zeka **10 milisaniye içinde** ilacın bağlanma gücünü (pKd değeri) hesaplıyor!

![NeoBioAI](https://img.shields.io/badge/Status-Completed-success) ![Machine Learning](https://img.shields.io/badge/ML-PyTorch%20Geometric-blue) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black)

---

## 🌟 Neden Önemli?
- **Geleneksel Yöntemler (AutoDock Vina vb.):** Her molekül için yaklaşık **2.5 saniye** sürer.
- **NeoBioAI (Bizim Modelimiz):** GINEConv GNN (Graf Sinir Ağı) mimarisi sayesinde molekül başına ortalama **4 milisaniye** sürer. Geleneksel yöntemlerden **600 kat daha hızlıdır!**

---

## 🚀 Proje Neler İçeriyor?

Proje 3 temel bacaktan oluşur ve tam çalışır bir platformdur:

1. **🧠 Yapay Zeka (GNN Modeli):** Molekülün atomlarını ve bağlarını 3 boyutlu bir "graf" ağına çevirip analiz eden (GINEConv) Python yapısı. PDBBind v2020 veri setindeki binlerce molekülle eğitilmiştir.
2. **⚙️ Backend API (FastAPI):** Modelin dış dünyayla konuşmasını sağlayan sunucu. Güvenlik için JWT altyapısı, token sistemi ve hız kısıtlaması (rate-limit) içerir.
3. **🖥️ Frontend Yüzü (Next.js):** Kullanıcıların kod bilmeden, güzel ve "akademik lacivert" temalı bir arayüzden yapay zekayı kullanmalarını sağlayan web sitesi.

---

## 💻 Kendi Bilgisayarında Adım Adım Çalıştırma (Sıfırdan)

Daha önce hiç yazılım çalıştırmamış biri bile bu adımlarla projeyi başlatabilir.

### Ön Koşullar:
- Bilgisayarınızda **Python (3.10 veya 3.11)** yüklü olmalı.
- **Node.js** (Next.js frontend için) yüklü olmalı.

### Adım 1: Klasöre Girin
Terminali (veya komut istemcisi - cmd) açın ve bu projenin bulunduğu klasöre (neodock) gidin.

### Adım 2: Backend'i (Yapay Zeka Sunucusunu) Başlatın
Sizin için hazırlanan otomatik başlama dosyasını çift tıklayarak veya terminalden çalıştırın:
- **Windows:** `start_backend.bat` 
- Veya manuel komut: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`

Ekrandaki yazılarda `Uvicorn running on http://0.0.0.0:8000` yazısını göreceksiniz. Backend arka planda açık kalmalı, **o siyah ekranı kapatmayın.**

### Adım 3: Frontend'i (Görsel Arayüzü) Başlatın
**Yeni/İkinci** bir terminal açın ve yine otomatik başlama dosyasını çalıştırın:
- **Windows:** `start_frontend.bat`
- Veya manuel komut: klasör içinde `cd frontend` yazıp ardından `npm install` ve sonrasında `npm run dev` yapın.

### Adım 4: Kullanmaya Başlayın!
Her şey hazır. Tarayıcınızı açın ve şu adreslere gidin:
- 🌐 **Ana Sayfa:** [http://localhost:3000](http://localhost:3000)
- 🧪 **Dashboard (Tahmin Paneli):** [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- 📚 **API Swagger Dokümanı:** [http://localhost:8000/docs](http://localhost:8000/docs)

*(Demo hesap için E-Posta: `demo@neodock.dev` Şifre: `demo1234` kullanabilirsiniz)*

---

## 🔬 Nasıl Test Edebilirim?

Dashboard paneline girdikten sonra moleküllerin "SMILES" formülünü yazmalısınız (Bu, kimyasal formüllerin metin halidir). İşte deneyebileceğiniz bazı örnekler:

| Molekül Adı | Ne İşe Yarar? | SMILES Kodu | Beklenen pKd Sonucu |
|------------|--------------|-------------|--------------------|
| **Aspirin** | Zayıf Ağrı Kesici | `CC(=O)Oc1ccccc1C(=O)O` | ~4.2 (Zayıf Bağlanma) |
| **Ibuprofen** | Orta Şiddetli Ağrı Kesici | `CC(C)Cc1ccc(cc1)C(C)C(=O)O` | ~5.9 (Orta Bağlanma) |
| **Imatinib**| Çok Güçlü Kanser İlacı | `Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C`| ~7.9 (Güçlü/İlaç Adayı) |

Sonuçlar yapay zekanın 50-60 milisaniye (ekranın yüklenmesi dahil) gibi inanılmaz bir sürede bu formülün hedef proteine ne kadar güçlü yapışacağını tahmin ettiğini gösterecektir. Değer ne kadar büyükse, bağlanma (ve ilaç potansiyeli) o kadar iyidir.

---

## 📁 Proje Dosya Yapısı (Geliştiriciler İçin)

```text
neodock/
├── backend/                    # FastAPI sunucu dosyaları (Route'lar, JWT vb.)
├── ml/                         # Yapay Zeka (GNN) modeli dosyaları ve eğitim kodları
├── frontend/                   # Next.js / TailwindCSS modern web sitesi
├── tests/                      # Otomatik API hata yakalama testleri
├── demo/                       # Jüriye komut satırından otomatik demo gösterme dosyası
├── start_backend.bat           # Çift tıkla başlat: Sunucu
└── start_frontend.bat          # Çift tıkla başlat: Arayüz
```

Bu proje, akademik bir çalışmanın laboratuvar metriklerinden gerçek dünya uygulamasına kadar nasıl inşa edilebileceğini kanıtlayan "production-ready" (kullanıma hazır) bir prototiptir.

---

## 📜 Lisans & Sahiplik

Bu proje **MIT Lisansı** ile sunulmaktadır.
Bu lisans kapsamında kaynak kodlar indirilebilir, incelenebilir ve açık kaynaklı/akademik projelerde atıf yapılarak kullanılabilir.

*Geliştirici: **Taykuth** (NeoBioAI Research)*
