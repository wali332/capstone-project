import { motion } from 'framer-motion';

export default function Trust() {
  const stats = [
    { label: 'DOMAIN', desc: 'Artificial Intelligence · Audio Signal Processing · Cybersecurity' },
    { label: 'DATASET', desc: 'Trained on ASVspoof 2019 LA — industry standard anti-spoofing benchmark' },
    { label: 'TECH STACK', desc: 'Python · PyTorch · Librosa · FastAPI · React · NumPy' },
  ];

  return (
    <section id="trust" className="w-full py-32 bg-brand-surface relative">
      <div className="container mx-auto px-8 max-w-4xl flex flex-col items-center">
        
        <motion.h2 
          className="font-sans font-bold text-[28px] text-white mb-16 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          Built for the age of synthetic media
        </motion.h2>

        <div className="w-full max-w-3xl flex flex-col gap-6 mb-20">
          {stats.map((stat, i) => (
            <motion.div 
              key={i}
              className="flex flex-col md:flex-row items-baseline justify-between border-b border-brand-border pb-4"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
            >
              <span className="font-mono text-[13px] text-brand-accent tracking-wide md:w-1/3 mb-2 md:mb-0">
                {stat.label}
              </span>
              <span className="font-sans text-[14px] text-gray-400 md:w-2/3 md:text-right">
                {stat.desc}
              </span>
            </motion.div>
          ))}
        </div>

        <motion.div 
          className="w-full max-w-3xl flex flex-col gap-4"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="bg-brand-base border border-brand-border rounded-[8px] p-8 relative overflow-hidden">
            {/* Subtle glow */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-brand-accent to-transparent opacity-50" />
            
            <div className="font-mono text-[13px] text-gray-400 leading-relaxed italic">
              <span className="text-gray-600 mr-2">//</span>
              "Most high-accuracy systems require heavy computation and large datasets,
              <br />
              <span className="text-gray-600 mr-2">//</span>
              &nbsp;&nbsp;reducing real-world feasibility for lightweight integration."
              <br />
              <span className="text-gray-600 mr-2">//</span>
              &nbsp;&nbsp;— Literature review finding, Team T-1-12-47-49
            </div>
          </div>

          {/* Research Summary Block */}
          <div className="font-mono text-[12px] text-gray-500 text-center tracking-wide mt-2">
            8 papers reviewed &nbsp;·&nbsp; 2016–2024 &nbsp;·&nbsp; ICASSP · IEEE · arXiv
          </div>
        </motion.div>

      </div>
    </section>
  );
}
