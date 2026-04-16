# VoiceGuard - Deepfake Audio Detection Platform

VoiceGuard is a modern, high-performance landing page and interactive mockup for a deepfake audio detection service. It provides a highly visual, animated experience that simulates the upload and analysis of audio files using deep learning (mel spectrogram inference) concepts.

## 🛠️ Technology Stack

1. **Core:** React 19
2. **Build Tool:** Vite
3. **Styling:** Tailwind CSS (Custom configured with a dark UI theme)
4. **Animations:** Framer Motion (Scroll reveals, layout animations, interactions)
5. **Utility Libraries:** `clsx`, `tailwind-merge` (for dynamic class name composition)

## 📁 Project Structure

The project follows a standard React SPA structure:

```text
capstone/
├── public/                 # Static assets (like spectrogram.png)
├── src/
│   ├── components/         # Modular UI sections
│   │   ├── Navbar.jsx      # Top navigation map
│   │   ├── Hero.jsx        # First viewport hero section
│   │   ├── HowItWorks.jsx  # Process explanation
│   │   ├── LiveDemo.jsx    # Interactive file upload and mock-analysis tool
│   │   ├── Technology.jsx  # Model details explanation
│   │   ├── Trust.jsx       # Social proof / trusted by logos
│   │   ├── About.jsx       # About the company/product
│   │   └── Footer.jsx      # Bottom footer
│   ├── App.jsx             # Main composition of all components
│   ├── main.jsx            # React root injection point
│   ├── index.css           # Tailwind base styles and directives
│   └── App.css             # Additional custom styles
├── tailwind.config.js      # Custom theme and brand colors
├── vite.config.js          # Vite configuration
└── package.json            # Project dependencies and scripts
```

## 🧩 How It Works (Under the Hood)

### 1. User Interface & Theming
The project uses a custom Tailwind CSS configuration (`tailwind.config.js`) tailored for a  primarily featuring dark palettes (`brand-base`, `brand-surface`), accented with vivid violet (`6C63FF`), mint green for authentic labels (`00E5A0`), and red/danger colors for fake labels (`FF4D6D`). Typography incorporates `JetBrains Mono` and `Inter`.

### 2. Live Demo Interactions
The core highlight of this project is the **Live Demo Section** (`src/components/LiveDemo.jsx`), which simulates an AI backend processing pipeline. Here is how it behaves:

- **State Machine:** The component operates in three primary states: `IDLE`, `ANALYZING`, and `RESULTS`.
- **Drag & Drop / Upload:** Users can click or drag-and-drop simulated audio files (`.wav`, `.mp3`, `.flac`).
- **Simulated Inference (`ANALYZING`):** Once a file is uploaded, a mock terminal actively logs processing steps (e.g., "extracting mel spectrogram...", "running cnn inference..."). It uses `setInterval` to print mock messages every 300ms to mimic a real backend.
- **Results (`RESULTS`):** Evaluates the file using pseudo-random logic:
  - Generates a random split (e.g., 85% Fake / 15% Real).
  - Classifies the file as `AI GENERATED` or `HUMAN VOICE`.
  - Performs CSS animations (like `borderFlashFake` or `crtFlicker`) to highlight the decision.
  - Updates a progress bar mimicking the probability scores using Framer Motion logic.

### 3. Animations
Framer Motion is heavily utilized to enhance the premium feel:
- **Scroll Animations:** Sections use `whileInView` variations to gently fade and slide up components as the user scrolls.
- **Micro-interactions:** Items like the scanning lines or drag-and-drop borders animate natively depending on user hover states and component lifecycles.

## 🚀 Running the Project Locally

To run the application on your machine:

1. **Install dependencies:**
   ```bash
   npm install
   ```
2. **Start the development server:**
   ```bash
   npm run dev
   ```
3. **Build for production:**
   ```bash
   npm run build
   ```

## 📝 Summary
VoiceGuard currently serves as a frontend-only interactive template. It is fully responsive, highly animated, and effectively mimics full-stack behavior through sophisticated React state management without needing an actual backend API.
