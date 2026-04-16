import { motion } from 'framer-motion';

export default function About() {
  const needs = [
    { label: "CALL CENTERS", desc: "Identify and prevent voice-based fraud and impersonation" },
    { label: "RECRUITMENT", desc: "Ensure authenticity in online interviews and assessments" },
    { label: "EXAMINATIONS", desc: "Verify candidate identity and prevent unauthorized assistance" },
    { label: "FORENSICS", desc: "Assist investigations involving synthetic media and deepfakes" }
  ];

  return (
    <section id="about-problem" className="w-full py-32 bg-brand-base relative overflow-hidden">
      <div className="container mx-auto px-8 max-w-6xl flex flex-col md:flex-row items-start justify-between gap-16">
        
        {/* Left Column */}
        <motion.div 
          className="w-full md:w-[45%] flex flex-col"
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="font-mono text-[11px] text-brand-violet uppercase tracking-widest mb-6 border-b border-brand-violet/30 pb-2 inline-block max-w-max">
            THE PROBLEM
          </span>
          <p className="font-sans text-[15px] text-gray-400 leading-relaxed">
            Recent advancements in Generative AI have enabled highly realistic synthetic voices 
            using TTS systems. These AI-generated voices are being misused for impersonation, 
            fraud, misinformation, and identity manipulation — and traditional verification 
            systems cannot keep up.
          </p>
        </motion.div>

        {/* Right Column */}
        <motion.div 
          className="w-full md:w-[50%] flex flex-col gap-8"
          initial={{ opacity: 0, x: 30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {needs.map((item, idx) => (
            <div key={idx} className="flex flex-col md:flex-row md:items-baseline gap-2 pb-4 border-b border-brand-border last:border-b-0">
               <div className="font-mono text-[13px] text-brand-violet tracking-wide md:w-1/3">
                 {item.label}
               </div>
               <div className="font-sans text-[14px] text-gray-400 md:w-2/3">
                 {item.desc}
               </div>
            </div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
