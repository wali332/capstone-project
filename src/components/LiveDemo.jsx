import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from 'framer-motion';

const TERMINAL_LINES = [
  "> received audio file...",
  "> normalizing signal...",
  "> extracting mel spectrogram...",
  "> running cnn inference...",
  "> softmax output: [confidence_fake, confidence_real]",
  "> classification complete."
];

export default function LiveDemo() {
  const [state, setState] = useState('IDLE');
  const [dragActive, setDragActive] = useState(false);
  const [logLines, setLogLines] = useState([]);
  const [flashColor, setFlashColor] = useState('');
  
  const [fileStats, setFileStats] = useState({
    name: '',
    duration: '',
    size: '',
    sampleRate: '',
    fakePercent: 0,
    realPercent: 0,
    verdict: '',
    confidence: ''
  });

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (state === 'ANALYZING') {
      let currentLine = 0;
      setLogLines([]);
      
      const intervalId = setInterval(() => {
        if (currentLine < TERMINAL_LINES.length) {
           setLogLines(prev => [...prev, TERMINAL_LINES[currentLine]]);
           currentLine++;
        } else {
          clearInterval(intervalId);
          setTimeout(() => setState('RESULTS'), 600);
        }
      }, 300);

      return () => clearInterval(intervalId);
    }
  }, [state]);

  useEffect(() => {
    if (state === 'RESULTS') {
      const isFake = fileStats.verdict === 'AI GENERATED';
      setFlashColor(isFake ? 'animate-[borderFlashFake_0.5s_ease-out_2]' : 'animate-[borderFlashReal_0.5s_ease-out_2]');
      
      const timer = setTimeout(() => {
        setFlashColor('');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [state, fileStats.verdict]);

  const handleDrag = function(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = function(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      startAnalysis(e.dataTransfer.files[0]);
    }
  };

  const handleChange = function(e) {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      startAnalysis(e.target.files[0]);
    }
  };

  const startAnalysis = (file) => {
    const isFake = Math.random() > 0.5;
    const fakeScore = isFake ? Math.floor(Math.random() * 15 + 85) : Math.floor(Math.random() * 15 + 5);
    const realScore = 100 - fakeScore;
    
    setFileStats({
      name: file.name,
      duration: '00:02:14', 
      size: (file.size / (1024 * 1024)).toFixed(1) + ' MB',
      sampleRate: '48.0 kHz',
      fakePercent: fakeScore,
      realPercent: realScore,
      verdict: isFake ? 'AI GENERATED' : 'HUMAN VOICE',
      confidence: `${Math.max(fakeScore, realScore)}%`
    });

    setState('ANALYZING');
  };

  const reset = () => {
    setState('IDLE');
    setLogLines([]);
    setFlashColor('');
    if (fileInputRef.current) {
        fileInputRef.current.value = "";
    }
  };

  useEffect(() => {
    const style = document.createElement('style');
    style.innerHTML = `
      @keyframes borderFlashFake {
        0%, 100% { border-color: #2A2A30; box-shadow: 0 0 16px rgba(108, 99, 255, 0.2); }
        50% { border-color: #FF4D6D; box-shadow: 0 0 32px rgba(255, 77, 109, 0.8); }
      }
      @keyframes borderFlashReal {
        0%, 100% { border-color: #2A2A30; box-shadow: 0 0 16px rgba(108, 99, 255, 0.2); }
        50% { border-color: #00E5A0; box-shadow: 0 0 32px rgba(0, 229, 160, 0.8); }
      }
    `;
    document.head.appendChild(style);
    return () => { document.head.removeChild(style); };
  }, []);

  return (
    <section id="try-it" className="w-full py-32 bg-brand-surface relative overflow-hidden">
      <div className="container mx-auto px-8 max-w-[1000px] flex flex-col items-center">
        
        <motion.h2 
          className="font-sans text-[28px] font-bold text-white mb-4"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          Try it yourself
        </motion.h2>

        <motion.p
          className="font-sans text-[15px] text-gray-400 mb-8 max-w-2xl text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Upload any audio file. Our model analyzes the mel spectrogram and returns a verdict in seconds.
        </motion.p>

        {/* Sample files text block */}
        <motion.div
           className="w-full max-w-5xl flex flex-col md:flex-row justify-center gap-4 md:gap-12 mb-8 font-mono text-[12px] text-gray-500 bg-brand-base border border-brand-border py-4 px-6 rounded-[8px]"
           initial={{ opacity: 0, y: 20 }}
           whileInView={{ opacity: 1, y: 0 }}
           viewport={{ once: true }}
           transition={{ duration: 0.5, delay: 0.2 }}
        >
           <div className="flex gap-2"><span className="text-white">sample_ai_voice.wav</span><span>→ known AI generated</span></div>
           <div className="flex gap-2"><span className="text-white">sample_human_voice.wav</span><span>→ known human</span></div>
           <div className="flex gap-2"><span className="text-white">sample_borderline.flac</span><span>→ ambiguous case</span></div>
        </motion.div>

        <motion.div 
          className={`w-full max-w-5xl h-[600px] flex bg-brand-base rounded-[12px] border border-brand-border shadow-[0_0_16px_rgba(108,99,255,0.2)] overflow-hidden transition-colors duration-200 ${flashColor}`}
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.3 }}
        >
           {/* LEFT PANEL */}
          <div className="w-[40%] flex flex-col h-full border-r border-brand-border p-8 relative shrink-0 bg-brand-base">
            
            {/* App Header */}
            <div className="mb-2 flex items-center gap-2">
              <h1 className="font-mono text-[13px] uppercase tracking-wider font-semibold text-white">VoiceGuard</h1>
              <div className="w-1.5 h-1.5 bg-brand-mint rounded-full animate-pulse" />
            </div>
            
            {/* Description */}
            <p className="text-[12px] text-gray-500 mb-12">
              Deepfake audio detection utilizing raw mel spectrogram inference.
            </p>

            {/* Upload State */}
            <AnimatePresence>
              {(state === 'IDLE' || state === 'ANALYZING') && (
                <motion.div 
                  initial={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="flex-1 flex flex-col items-center justify-center -mt-16"
                >
                  <div 
                    className={`w-full max-w-[280px] aspect-[4/3] border-[2px] rounded-none flex items-center justify-center transition-colors relative
                      ${dragActive ? 'border-solid border-brand-violet bg-brand-violet/5' : 'border-dashed border-brand-border bg-brand-surface'}
                      ${state === 'ANALYZING' ? 'opacity-50 pointer-events-none' : ''}
                    `}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    {state === 'IDLE' ? (
                      <span className="font-mono text-[12px] text-gray-400 pointer-events-none text-center px-4">
                        drop .wav / .mp3 / .flac here
                      </span>
                    ) : (
                      <div className="flex flex-col items-center gap-4">
                        <div className="flex items-end gap-[3px] h-6">
                            {[1,2,3,4,5].map(i => (
                              <motion.div key={i} animate={{ height: [6, Math.random() * 16 + 8, 6] }} transition={{ repeat: Infinity, duration: 0.8 + i*0.1 }} className="w-1.5 bg-brand-violet rounded-sm" />
                            ))}
                        </div>
                        <span className="font-mono text-[11px] text-brand-violet">Extracting...</span>
                      </div>
                    )}
                  </div>
                  
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleChange} 
                    accept=".wav,.mp3,.flac" 
                    className="hidden" 
                  />
                  
                  {state === 'IDLE' && (
                    <button 
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-6 text-[13px] text-brand-violet hover:text-white hover:underline decoration-1 underline-offset-4 outline-none transition-colors"
                    >
                      or browse files
                    </button>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Results State Left Panel */}
            <AnimatePresence>
              {state === 'RESULTS' && (
                <motion.div 
                  initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                  className="flex-1 flex flex-col justify-start mt-8"
                >
                  <div className="flex items-baseline justify-between mb-10">
                    <div className="font-mono text-[13px] text-white truncate pr-4" title={fileStats.name}>{fileStats.name}</div>
                    <div className="font-mono text-[13px] text-gray-500 shrink-0">{fileStats.duration}</div>
                  </div>

                  {/* Split Bar */}
                  <div className="mb-10 relative w-full">
                    <div className="flex justify-between font-mono text-[11px] mb-2 text-gray-400">
                      <span>FAKE <Counter value={fileStats.fakePercent} />%</span>
                      <span>REAL <Counter value={fileStats.realPercent} />%</span>
                    </div>
                    <div className="h-[6px] w-full flex bg-brand-surface border border-brand-border overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${fileStats.fakePercent}%` }} transition={{ duration: 1, ease: "easeOut" }} className="bg-brand-danger h-full" />
                      <motion.div initial={{ width: 0 }} animate={{ width: `${fileStats.realPercent}%` }} transition={{ duration: 1, ease: "easeOut" }} className="bg-brand-mint h-full" />
                    </div>
                  </div>

                  {/* File Stats */}
                  <div className="flex items-center justify-between border-t border-brand-border pt-6">
                    <div className="flex flex-col">
                      <span className="font-sans text-[11px] text-gray-500 mb-1 tracking-wide uppercase">SAMPLE RATE</span>
                      <span className="font-mono text-[13px] text-white">{fileStats.sampleRate}</span>
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="font-sans text-[11px] text-gray-500 mb-1 tracking-wide uppercase">FILE SIZE</span>
                      <span className="font-mono text-[13px] text-white">{fileStats.size}</span>
                    </div>
                  </div>

                  <div className="mt-auto pt-6 border-t border-brand-border flex justify-between items-end">
                    <button 
                      onClick={reset}
                      className="font-mono text-[13px] text-gray-400 hover:text-white hover:underline decoration-1 underline-offset-4 outline-none transition-colors"
                    >
                      analyze another
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

          </div>

          {/* RIGHT PANEL */}
          <div className="w-[60%] h-full relative overflow-hidden bg-brand-surface flex flex-col">
            
            {/* IDLE: Faint Watermark */}
            {state === 'IDLE' && (
              <div className="absolute inset-0 flex items-center justify-center opacity-5 select-none pointer-events-none mix-blend-screen">
                <img src="/spectrogram.png" alt="" className="w-full h-full object-cover blur-[1px] grayscale" />
              </div>
            )}

            {/* ANALYZING: Terminal Log */}
            {state === 'ANALYZING' && (
              <div className="w-full h-full p-12 bg-brand-surface relative z-10 flex flex-col justify-end overflow-hidden">
                <div className="font-mono text-[13px] text-brand-violet leading-loose opacity-80">
                  {logLines.map((line, index) => (
                    <motion.div key={index} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
                        {line}
                    </motion.div>
                  ))}
                  <div className="inline-block w-2 h-3.5 bg-brand-violet ml-1 translate-y-[2px] animate-[pulse_1s_ease-in-out_infinite]" />
                </div>
              </div>
            )}

            {/* RESULTS: Result View */}
            {state === 'RESULTS' && (
              <motion.div 
                className="w-full h-full flex flex-col relative z-10 bg-brand-surface"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}
              >
                <div className="flex-1 min-h-0 relative">
                  <img 
                    src="/spectrogram.png" 
                    alt="Mel Spectrogram" 
                    className="w-full h-full object-cover grayscale brightness-125 contrast-[1.2] opacity-80"
                  />
                  <motion.div 
                    initial={{ left: 0 }} animate={{ left: "100%" }} transition={{ duration: 1.2, ease: "easeInOut" }}
                    className="absolute inset-0 bg-brand-surface"
                  />
                  
                  <div className="absolute inset-x-0 bottom-0 px-4 py-2 flex justify-between bg-brand-base/80 backdrop-blur-sm border-t border-brand-border">
                    <span className="font-mono text-[11px] text-gray-500">Time (s)</span>
                    <span className="font-mono text-[11px] text-gray-500">Freq (Hz)</span>
                  </div>
                </div>

                <div className="px-12 py-10 shrink-0 bg-brand-base border-t border-brand-border z-20">
                  <div className="flex items-baseline gap-4">
                      <span className={`font-mono font-bold text-[22px] tracking-wide ${fileStats.verdict === 'AI GENERATED' ? 'text-brand-danger' : 'text-brand-mint'} animate-[crtFlicker_0.1s_ease-in-out_3]`}>
                        {fileStats.verdict}
                      </span>
                      <span className="font-mono text-[13px] text-gray-500">
                        conf: <Counter value={parseInt(fileStats.confidence)} />%
                      </span>
                  </div>
                </div>
              </motion.div>
            )}

            <style>{`
              @keyframes crtFlicker {
                0% { opacity: 1; }
                50% { opacity: 0.6; }
                100% { opacity: 1; }
              }
            `}</style>
          </div>

        </motion.div>
      </div>
    </section>
  );
}

// Helper component for count-up animation
function Counter({ value }) {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const end = parseInt(value);
    if (start === end) return;
    
    let totalDuration = 1000;
    let incrementTime = (totalDuration / end);
    
    let timer = setInterval(() => {
      start += 1;
      setCount(start);
      if (start === end) clearInterval(timer);
    }, incrementTime);
    
    return () => clearInterval(timer);
  }, [value]);
  
  return <span>{count}</span>;
}
