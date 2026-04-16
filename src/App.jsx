import Navbar from './components/Navbar';
import Hero from './components/Hero';
import HowItWorks from './components/HowItWorks';
import LiveDemo from './components/LiveDemo';
import Technology from './components/Technology';
import Trust from './components/Trust';
import About from './components/About';
import Footer from './components/Footer';

function App() {
  return (
    <div className="w-full min-h-screen bg-brand-base text-white font-sans selection:bg-brand-violet/30 selection:text-white">
      <Navbar />
      <Hero />
      <HowItWorks />
      <LiveDemo />
      <Technology />
      <Trust />
      <About />
      <Footer />
    </div>
  );
}

export default App;
