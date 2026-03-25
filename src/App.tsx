import { useEffect, useState } from 'react';
import Header from './sections/Header';
import Hero from './sections/Hero';
import CollaboratorsBanner from './sections/CollaboratorsBanner';
import GlobalReach from './sections/GlobalReach';
import ProjectShowcase from './sections/ProjectShowcase';
import Services from './sections/Services';
import Intro from './sections/Intro';
import Testimonials from './sections/Testimonials';
import CTA from './sections/CTA';
import Footer from './sections/Footer';
import CustomCursor from '@/components/ui/custom-cursor';
import LoadingScreen from '@/components/ui/loading-screen';

export default function App() {
  const [loadingDone, setLoadingDone] = useState(false);
  const [scrambleReady, setScrambleReady] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setScrambleReady(true), 1500);
    return () => clearTimeout(t);
  }, []);

  return (
    <main className="relative">
      <LoadingScreen onComplete={() => setLoadingDone(true)} />
      <CustomCursor />
      <Header />
      <Hero loadingDone={scrambleReady} />       {/* 1 */}
      <CollaboratorsBanner />                     {/* 2 */}
      <GlobalReach />                             {/* 3 */}
      <ProjectShowcase />                         {/* 4 */}
      <Services />                                {/* 3 */}
      <Intro />                                   {/* 4 */}
      <Testimonials />                            {/* 5 */}
      <CTA />                                     {/* 6 */}
      <Footer />
    </main>
  );
}
