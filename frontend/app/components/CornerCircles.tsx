import LogoCircle from './LogoCircle';

export default function CornerCircles() {
  return (
    <>
      {/* Top left */}
      <div className="fixed top-6 left-6 z-20">
        <LogoCircle />
      </div>
      {/* Top right */}
      <div className="fixed top-6 right-6 z-20">
        <LogoCircle />
      </div>
      {/* Bottom left (mid-left in design) */}
      <div className="fixed bottom-1/2 left-6 z-20 translate-y-1/2">
        <LogoCircle />
      </div>
      {/* Bottom right (mid-right in design): slight blur + slow circular rotation */}
      <div className="fixed bottom-1/2 right-6 z-20 translate-y-1/2 corner-circle-blur-rotate">
        <LogoCircle />
      </div>
    </>
  );
}
