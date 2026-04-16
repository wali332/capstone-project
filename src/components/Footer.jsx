export default function Footer() {
  return (
    <footer className="w-full bg-brand-base border-t border-brand-border py-8 px-8">
      <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        <div className="font-sans font-semibold text-[14px] text-white tracking-wide text-left flex-1">
          VoiceGuard
        </div>
        
        <div className="font-mono text-[12px] text-gray-500 text-center flex-1">
          PES University · BCA Capstone 2025 · Team T-1-12-47-49
        </div>

        <div className="font-sans text-[12px] text-gray-400 text-right flex-1 flex md:justify-end gap-x-2 whitespace-normal md:whitespace-nowrap flex-wrap">
          <span>Abdul Wali</span>
          <span className="opacity-50">·</span>
          <span>Dhruva S</span>
          <span className="opacity-50">·</span>
          <span>Farhan Patel</span>
          <span className="opacity-50">·</span>
          <span>Akshobya</span>
        </div>

      </div>
    </footer>
  );
}
