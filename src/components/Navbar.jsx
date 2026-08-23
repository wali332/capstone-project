import { motion } from 'framer-motion';

export default function Navbar() {
  return (
    <motion.nav 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="fixed top-0 inset-x-0 h-[56px] bg-brand-base/80 backdrop-blur-[12px] border-b border-brand-border z-50 flex items-center justify-between px-8"
    >
      <div className="flex items-center gap-3">
        {/* Animated Waveform SVG Logo */}
        <div className="flex items-end gap-[2px] h-4">
          <motion.div animate={{ height: [6, 12, 6] }} transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }} className="w-1 bg-brand-accent rounded-full" />
          <motion.div animate={{ height: [8, 16, 8] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.2, ease: "easeInOut" }} className="w-1 bg-brand-accent/80 rounded-full" />
          <motion.div animate={{ height: [4, 10, 4] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.4, ease: "easeInOut" }} className="w-1 bg-brand-accent/60 rounded-full" />
          <motion.div animate={{ height: [10, 16, 10] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.6, ease: "easeInOut" }} className="w-1 bg-brand-accent/80 rounded-full" />
          <motion.div animate={{ height: [6, 12, 6] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.8, ease: "easeInOut" }} className="w-1 bg-brand-accent rounded-full" />
        </div>
        <span className="font-sans font-semibold text-[15px] text-white tracking-wide">
          VoiceGuard
        </span>
      </div>

      <div className="hidden md:flex items-center gap-8">
        {['How it works', 'Technology', 'Try it', 'About'].map((item) => (
          <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} className="group relative font-sans text-[13px] text-gray-400 hover:text-white transition-colors duration-200">
            {item}
            <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-brand-accent transition-all duration-300 group-hover:w-full"></span>
          </a>
        ))}
      </div>

      <div>
        <button className="bg-brand-accent text-white text-[13px] font-medium px-4 py-1.5 rounded-[6px] hover:shadow-[0_0_16px_#22D3EE55] transition-all duration-300">
          Try for free
        </button>
      </div>
    </motion.nav>
  );
}
