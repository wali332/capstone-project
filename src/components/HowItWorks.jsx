import { motion } from 'framer-motion';

export default function HowItWorks() {
  const steps = [
    {
      title: "Upload audio",
      desc: "Accepts recorded .wav, .mp3, or .flac files. Signal is normalized and enhanced for optimal quality before processing.",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-brand-violet">
          <path d="M12 16V4M12 4L8 8M12 4L16 8M4 20H20" />
        </svg>
      )
    },
    {
      title: "Spectrogram extracted",
      desc: "Audio is transformed into a 2D time-frequency visual using mel filterbanks. AI voices leave distinct spectral artifacts invisible to human ears.",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6 text-brand-violet">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9H21M3 15H21M9 3V21M15 3V21" />
        </svg>
      )
    },
    {
      title: "Deep learning analysis",
      desc: "A trained Convolutional Neural Network reads spectral patterns and classifies speech as human or AI with a quantifiable confidence score.",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-6 h-6 text-brand-violet">
          <rect x="4" y="4" width="6" height="16" rx="1" />
          <rect x="14" y="6" width="6" height="12" rx="1" />
          <path d="M10 12h4" strokeDasharray="2 2" />
        </svg>
      )
    }
  ];

  const pipelineNodes = [
    "RAW AUDIO", "NORMALIZATION", "MEL SPECTROGRAM", "CNN MODEL", "SOFTMAX", "VERDICT"
  ];

  return (
    <section id="how-it-works" className="w-full py-32 bg-brand-base overflow-hidden">
      <div className="container mx-auto px-8 max-w-6xl">
        
        {/* Section Title */}
        <div className="flex flex-col items-center mb-24">
          <h2 className="font-sans text-[32px] font-bold text-white mb-4 relative inline-block">
            How VoiceGuard works
            <motion.div 
              className="absolute -bottom-2 left-0 h-[2px] bg-brand-violet"
              initial={{ width: 0 }}
              whileInView={{ width: "100%" }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
            />
          </h2>
        </div>

        {/* Steps Grid */}
        <div className="flex flex-col md:flex-row gap-8 relative mb-32 z-10">
          {/* Connecting Line (desktop only) */}
          <div className="hidden md:block absolute top-[40px] left-[15%] right-[15%] h-[1px] border-t border-dashed border-brand-border -z-10" />

          {steps.map((step, idx) => (
            <motion.div 
              key={idx}
              className="flex-1 bg-brand-surface border border-brand-border rounded-[8px] p-6 relative"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: idx * 0.15 }}
            >
              {/* Icon Container */}
              <div className="w-12 h-12 rounded-full bg-brand-base border border-brand-border flex items-center justify-center mb-6 shadow-[0_0_12px_#6C63FF15]">
                {step.icon}
              </div>
              <h3 className="font-sans font-semibold text-white text-[16px] mb-2">{step.title}</h3>
              <p className="font-sans text-[13px] text-gray-400 leading-relaxed">{step.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Pipeline Diagram */}
        <motion.div 
          className="w-full relative"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
           <div className="flex flex-wrap md:flex-nowrap items-center justify-between relative px-4">
             {/* Background Line */}
             <div className="absolute top-1/2 left-8 right-8 h-px bg-brand-border -z-10 -translate-y-1/2 hidden md:block" />
             
             {/* Animated Signal Dot */}
             <motion.div 
               className="hidden md:block absolute top-1/2 left-8 w-2 h-2 rounded-full bg-brand-violet shadow-[0_0_8px_#6C63FF] -translate-y-1/2 z-0"
               animate={{ left: ["2%", "98%"] }}
               transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
             />

             {pipelineNodes.map((node, i) => (
               <div key={i} className="flex relative z-10 items-center my-2 md:my-0">
                 <div className="bg-brand-surface border border-brand-border px-3 py-1.5 rounded-[12px] font-mono text-[11px] text-gray-400 whitespace-nowrap">
                   {node}
                 </div>
                 {i < pipelineNodes.length - 1 && (
                   <div className="md:hidden w-4 h-px border-t border-dashed border-brand-border mx-2" />
                 )}
               </div>
             ))}
           </div>
        </motion.div>

      </div>
    </section>
  );
}
