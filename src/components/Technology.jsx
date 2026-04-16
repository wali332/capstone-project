import { motion } from 'framer-motion';

export default function Technology() {
  return (
    <section id="technology" className="w-full py-32 bg-brand-base relative overflow-hidden">
      <div className="container mx-auto px-8 max-w-6xl flex flex-col md:flex-row items-center justify-between gap-16">
        
        {/* Left Column */}
        <motion.div 
          className="w-full md:w-1/2 flex flex-col"
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="font-mono text-[11px] text-brand-violet uppercase tracking-widest mb-4">
            Under the hood
          </span>
          <h2 className="font-sans font-bold text-[32px] text-white mb-6">
            Not a black box.
          </h2>
          <p className="font-sans text-[15px] text-gray-400 leading-relaxed mb-12">
            Audio signals are converted into mel spectrograms — 2D time-frequency representations where the x-axis is time and y-axis is mel-scaled frequency. AI-generated voices produce unnaturally smooth frequency transitions and missing noise floors that a CNN learns to detect. Our lightweight architecture prioritizes computational feasibility and real-world deployability over raw benchmark performance.
          </p>

          <div className="flex gap-4">
            <div className="bg-brand-surface border border-brand-border rounded-[8px] p-4 flex-1">
              <div className="font-mono text-[14px] text-white">128×128 spectrogram input</div>
            </div>
            <div className="bg-brand-surface border border-brand-border rounded-[8px] p-4 flex-1">
              <div className="font-mono text-[14px] text-white">Lightweight CNN architecture</div>
            </div>
          </div>
        </motion.div>

        {/* Right Column (Animated CNN Architecture) */}
        <motion.div 
          className="w-full md:w-1/2 h-[300px] bg-brand-surface border border-brand-border rounded-[12px] flex items-center justify-center relative shadow-[inset_0_0_40px_rgba(0,0,0,0.5)]"
          initial={{ opacity: 0, x: 30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <svg viewBox="0 0 550 200" className="w-full h-full max-w-[450px]">
             {/* Base Lines */}
             <line x1="80" y1="100" x2="480" y2="100" stroke="#2A2A30" strokeWidth="2" strokeDasharray="4 4" />
             
             {/* Input Layer */}
             <rect x="40" y="70" width="40" height="60" rx="4" fill="#0D0D0F" stroke="#2A2A30" strokeWidth="2" />
             <text x="60" y="145" fontSize="8" fill="#6c757d" textAnchor="middle" fontFamily="monospace">INPUT</text>

             {/* Conv Layers block visual */}
             <g transform="translate(130, 0)">
               {[0, 1, 2].map((i) => (
                 <g key={i}>
                   <rect x={i * 35} y={60 + i*5} width="20" height={80 - i*10} rx="2" fill="#0D0D0F" stroke="#2A2A30" strokeWidth="2" />
                   {/* Animated Glow overlay */}
                   <motion.rect 
                     x={i * 35} y={60 + i*5} width="20" height={80 - i*10} rx="2" fill="none" stroke="#6C63FF" strokeWidth="2"
                     initial={{ opacity: 0 }}
                     animate={{ opacity: [0, 1, 1, 0] }}
                     transition={{ duration: 2, repeat: Infinity, times: [0, 0.2, 0.4, 1], delay: 0.3 * (i+1) }}
                     style={{ filter: "drop-shadow(0 0 8px #6C63FF)" }}
                   />
                 </g>
               ))}
               <text x="50" y="155" fontSize="8" fill="#6c757d" textAnchor="middle" fontFamily="monospace">CONV2D → RELU → MAXPOOL</text>
             </g>

             {/* Dense / Flatten Layer */}
             <g transform="translate(290, 0)">
               <rect x="0" y="80" width="30" height="40" rx="2" fill="#0D0D0F" stroke="#2A2A30" strokeWidth="2" />
               <motion.rect 
                 x="0" y="80" width="30" height="40" rx="2" fill="none" stroke="#6C63FF" strokeWidth="2"
                 initial={{ opacity: 0 }}
                 animate={{ opacity: [0, 1, 1, 0] }}
                 transition={{ duration: 2, repeat: Infinity, times: [0, 0.2, 0.4, 1], delay: 1.0 }}
                 style={{ filter: "drop-shadow(0 0 8px #6C63FF)" }}
               />
               <text x="15" y="145" fontSize="8" fill="#6c757d" textAnchor="middle" fontFamily="monospace">CONV2D → FLATTEN</text>
             </g>

             {/* Dense Layer */}
             <g transform="translate(400, 0)">
               <rect x="0" y="90" width="20" height="20" rx="2" fill="#0D0D0F" stroke="#2A2A30" strokeWidth="2" />
               <motion.rect 
                 x="0" y="90" width="20" height="20" rx="2" fill="none" stroke="#6C63FF" strokeWidth="2"
                 initial={{ opacity: 0 }}
                 animate={{ opacity: [0, 1, 1, 0] }}
                 transition={{ duration: 2, repeat: Infinity, times: [0, 0.2, 0.4, 1], delay: 1.3 }}
                 style={{ filter: "drop-shadow(0 0 8px #6C63FF)" }}
               />
               <text x="10" y="130" fontSize="8" fill="#6c757d" textAnchor="middle" fontFamily="monospace">DENSE</text>
             </g>

             {/* Output Node */}
             <g transform="translate(480, 0)">
               <circle cx="10" cy="100" r="10" fill="#0D0D0F" stroke="#2A2A30" strokeWidth="2" />
               <motion.circle 
                 cx="10" cy="100" r="10" fill="none" stroke="#6C63FF" strokeWidth="2"
                 initial={{ opacity: 0 }}
                 animate={{ opacity: [0, 1, 1, 0] }}
                 transition={{ duration: 2, repeat: Infinity, times: [0, 0.2, 0.4, 1], delay: 1.6 }}
                 style={{ filter: "drop-shadow(0 0 8px #6C63FF)" }}
               />
               <text x="10" y="125" fontSize="8" fill="#6c757d" textAnchor="middle" fontFamily="monospace">SOFTMAX</text>
             </g>

          </svg>
        </motion.div>

      </div>
    </section>
  );
}
