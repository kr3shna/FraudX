import Header from './components/Header';
import Hero from './components/Hero';
import CornerCircles from './components/CornerCircles';
import ThreeWays from './components/ThreeWays';
import FiveSteps from './components/FiveSteps';
import SuspicionScore from './components/SuspicionScore';
import ForensicResults from './components/ForensicResults';
import CSVUpload from './components/CSVUpload';
import Footer from './components/Footer';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#020202] text-white">
      <CornerCircles />
      <Header />
      {/* Hero: wave image fills the full section background */}
      <Hero />
      {/* ThreeWays: sits directly below on dark background */}
      <ThreeWays />
      <FiveSteps />
      <SuspicionScore />
      <ForensicResults />
      <CSVUpload />
      <Footer />
    </div>
  );
}