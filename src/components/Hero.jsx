import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

export default function Hero() {
  const [demoState, setDemoState] = useState(0);

  const demoCycles = [
    { file: "board_meeting_clip.wav", verdict: "AI GENERATED", conf: "91%", isFake: true },
    { file: "interview_recording.mp3", verdict: "HUMAN VOICE", conf: "96%", isFake: false },
    { file: "podcast_intro.flac", verdict: "AI GENERATED", conf: "84%", isFake: true }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setDemoState(prev => (prev + 1) % 3);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const currentDemo = demoCycles[demoState];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.15, delayChildren: 0.2 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 24 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
  };

  return (
    <section className="relative w-full min-h-screen flex items-center pt-20 overflow-hidden bg-brand-base">
      {/* Background Radial Glow */}
      <div className="absolute right-[20%] top-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-accent/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="container mx-auto px-8 max-w-7xl relative z-10 flex flex-col lg:flex-row items-center justify-between gap-16">
        
        {/* Left Side: 55% */}
        <motion.div 
          className="w-full lg:w-[55%] flex flex-col items-start"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {/* Pill */}
          <motion.div variants={itemVariants} className="inline-flex items-center px-4 py-1.5 rounded-[20px] bg-brand-accent/20 mb-8">
            <span className="font-sans text-[12px] text-brand-accent">BCA Capstone 2025 — Team T-1-12-47-49</span>
          </motion.div>

          {/* Heading */}
          <motion.h1 variants={itemVariants} className="font-sans font-bold text-[52px] text-white leading-[1.1] mb-6">
            Your ears can't catch it.<br />
            <span className="text-brand-accent">We can.</span>
          </motion.h1>

          {/* Subtext */}
          <motion.p variants={itemVariants} className="font-sans text-[16px] text-gray-400 max-w-lg mb-10 leading-relaxed">
            AI-generated voices are indistinguishable to humans. VoiceGuard converts audio into mel spectrograms and uses a trained CNN to detect synthetic speech patterns invisible to the naked ear.
          </motion.p>

          {/* Buttons */}
          <motion.div variants={itemVariants} className="flex items-center gap-4 mb-14">
            <button className="bg-brand-accent text-white font-medium text-[14px] px-6 py-3 rounded-[6px] hover:bg-brand-accent/90 transition-colors flex items-center gap-2">
              Analyze audio <span className="text-lg leading-none">→</span>
            </button>
            <button className="border border-brand-border text-white font-medium text-[14px] px-6 py-3 rounded-[6px] hover:bg-brand-border transition-colors">
              See how it works
            </button>
          </motion.div>

          {/* Stats */}
          <motion.div variants={itemVariants} className="flex items-center gap-6 text-[13px] font-mono text-gray-500 whitespace-nowrap overflow-hidden">
            <span>Binary Classification</span>
            <div className="w-px h-4 bg-brand-border" />
            <span>Mel Spectrogram + CNN</span>
            <div className="w-px h-4 bg-brand-border" />
            <span>FastAPI + React</span>
          </motion.div>
        </motion.div>

        {/* Right Side: 45% (Live Demo Card) */}
        <motion.div 
          className="w-full lg:w-[45%] relative"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
        >
          <div className="bg-brand-surface rounded-[12px] border border-brand-border overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.5)]">
            
            {/* Card Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-base">
              <div className="flex items-center gap-3">
                <div className="flex items-end gap-1 h-3">
                  {[1,2,3,4].map(i => (
                    <motion.div key={i} animate={{ height: [4, Math.random() * 12 + 4, 4] }} transition={{ repeat: Infinity, duration: 0.8 + i*0.1 }} className="w-1 bg-brand-accent rounded-full" />
                  ))}
                </div>
                <AnimatePresence mode="wait">
                  <motion.span 
                    key={currentDemo.file}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="font-mono text-[12px] text-gray-400"
                  >
                    {currentDemo.file}
                  </motion.span>
                </AnimatePresence>
              </div>
            </div>

            {/* Spectrogram / Analysis Area */}
            <div className="relative h-[200px] w-full bg-brand-base overflow-hidden">
               <div className="absolute inset-0 opacity-[0.15] bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.2)_50%,transparent_100%)] bg-[length:20px_100%]"/>
               <div className="absolute inset-0 flex flex-col justify-around py-4">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="w-full h-px bg-white/5" />
                  ))}
               </div>
               
               <motion.div 
                className="absolute top-0 bottom-0 left-0 w-32 bg-gradient-to-r from-transparent via-brand-accent/20 to-brand-accent/80 border-r border-brand-accent"
                animate={{ x: ["-10%", "400%"] }}
                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
               />
            </div>

            {/* Verdict Footer */}
            <div className="px-6 py-5 bg-brand-surface border-t border-brand-border h-[80px] flex items-center">
               <AnimatePresence mode="wait">
                 <motion.div 
                  key={currentDemo.verdict}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center gap-3 w-full"
                 >
                   <div className={`w-3 h-3 rounded-full ${currentDemo.isFake ? 'bg-brand-danger shadow-[0_0_8px_#FB7185]' : 'bg-brand-mint shadow-[0_0_8px_#34D399]'}`} />
                   <span className={`font-mono text-[20px] font-bold ${currentDemo.isFake ? 'text-brand-danger' : 'text-brand-mint'}`}>
                     {currentDemo.verdict}
                   </span>
                   <span className="ml-auto font-mono text-[12px] text-gray-500">
                     confidence: {currentDemo.conf}
                   </span>
                 </motion.div>
               </AnimatePresence>
            </div>

          </div>
        </motion.div>

      </div>
    </section>
  );
}
