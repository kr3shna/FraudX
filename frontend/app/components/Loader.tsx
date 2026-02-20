'use client';

import { useEffect, useMemo, useState } from 'react';
import { Space_Mono } from 'next/font/google';
import styles from './Loader.module.css';

const spaceMono = Space_Mono({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-loader-mono',
});

type PointTag = 'OK' | 'WARN' | 'ALERT' | 'DONE';

type Step = {
  titlePrefix: string;
  titleHighlight: string;
  subtitle: string;
  progress: number;
  points: Array<{ text: string; tag: PointTag }>;
};

const steps: Step[] = [
  {
    titlePrefix: 'Uploading',
    titleHighlight: 'Files',
    subtitle: 'Parsing transaction records...',
    progress: 0,
    points: [
      
    ],
  },
  {
    titlePrefix: 'Reading',
    titleHighlight: 'Data',
    subtitle: 'Extracting entity relationships...',
    progress: 25,
    points: [
      
    ],
  },
  {
    titlePrefix: 'Analyzing',
    titleHighlight: 'Information',
    subtitle: 'Running behavioral pattern models...',
    progress: 50,
    points: [
     
    ],
  },
  {
    titlePrefix: 'Making',
    titleHighlight: 'Nodes',
    subtitle: 'Building transaction graph topology...',
    progress: 75,
    points: [
     
    ],
  },
  {
    titlePrefix: 'Rendering',
    titleHighlight: 'Network',
    subtitle: 'Exposing the money mule rings...',
    progress: 100,
    points: [],
  },
];

const pointColors: Record<PointTag, string> = {
  OK: '#00e87b',
  WARN: '#ffb347',
  ALERT: '#ff4d4d',
  DONE: '#00e87b',
};

function iconClass(active: boolean) {
  return `${styles.stepIcon} ${active ? styles.active : ''}`;
}

export default function Loader() {
  const [currentStep, setCurrentStep] = useState(0);
  const [pointPhase, setPointPhase] = useState<Array<'hidden' | 'visible' | 'complete'>>(
    () => Array(steps[0].points.length).fill('hidden'),
  );

  const step = steps[currentStep];

  useEffect(() => {
    const timers: number[] = [];

    step.points.forEach((_, index) => {
      timers.push(
        window.setTimeout(() => {
          setPointPhase((prev) => {
            const next = [...prev];
            next[index] = 'visible';
            return next;
          });

          timers.push(
            window.setTimeout(() => {
              setPointPhase((prev) => {
                const next = [...prev];
                next[index] = 'complete';
                return next;
              });
            }, 300),
          );
        }, index * 320),
      );
    });

    const cycleTimer = window.setTimeout(() => {
      setCurrentStep((prev) => {
        const next = (prev + 1) % steps.length;
        setPointPhase(Array(steps[next].points.length).fill('hidden'));
        return next;
      });
    }, currentStep === steps.length - 1 ? 3000 : 2800);

    return () => {
      window.clearTimeout(cycleTimer);
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [currentStep, step.points]);

  const markerIndexes = useMemo(() => Array.from({ length: steps.length }, (_, i) => i), []);

  return (
    <div className={`${styles.loaderRoot} ${spaceMono.variable}`}>
      <div className={styles.loader}>
        <div className={styles.iconStage}>
          <div className={styles.ringOuter} />
          <div className={styles.ringMid} />
          <div className={`${styles.spark} ${styles.spark1}`} />
          <div className={`${styles.spark} ${styles.spark2}`} />
          <div className={`${styles.spark} ${styles.spark3}`} />
          <div className={styles.iconCore}>
            <div className={styles.scanLine} />

            <svg className={iconClass(currentStep === 0)} viewBox="0 0 52 52" fill="none" aria-hidden>
              <rect className={styles.iconFill} x="8" y="20" width="36" height="26" rx="3" />
              <rect className={styles.iconStroke} x="8" y="20" width="36" height="26" rx="3" />
              <path className={styles.iconStroke} d="M26 6v24M18 14l8-8 8 8" strokeWidth="2" strokeLinejoin="round" />
              <path className={styles.iconStroke} d="M16 42h20" />
              <circle cx="26" cy="36" r="2" fill="var(--loader-green)" opacity="0.6" />
            </svg>

            <svg className={iconClass(currentStep === 1)} viewBox="0 0 52 52" fill="none" aria-hidden>
              <rect className={styles.iconFill} x="6" y="10" width="32" height="36" rx="3" />
              <rect className={styles.iconStroke} x="6" y="10" width="32" height="36" rx="3" />
              <path className={styles.iconStroke} d="M13 20h18M13 27h14M13 34h10" />
              <circle cx="37" cy="37" r="8" fill="rgba(0,232,123,0.2)" />
              <circle className={styles.iconStroke} cx="37" cy="37" r="6" />
              <path className={styles.iconStroke} d="M41.5 41.5l4 4" strokeWidth="2" />
            </svg>

            <svg className={iconClass(currentStep === 2)} viewBox="0 0 52 52" fill="none" aria-hidden>
              <rect className={styles.iconFill} x="6" y="6" width="40" height="40" rx="4" />
              <rect className={styles.iconStroke} x="6" y="6" width="40" height="40" rx="4" />
              <path className={styles.iconStroke} d="M13 32l8-10 7 6 6-12 7 8" />
              <rect x="10" y="38" width="6" height="6" rx="1" fill="rgba(0,232,123,0.35)" />
              <rect className={styles.iconStroke} x="10" y="38" width="6" height="6" rx="1" />
              <rect x="23" y="32" width="6" height="12" rx="1" fill="rgba(0,232,123,0.25)" />
              <rect className={styles.iconStroke} x="23" y="32" width="6" height="12" rx="1" />
              <rect x="36" y="26" width="6" height="18" rx="1" fill="rgba(0,232,123,0.4)" />
              <rect className={styles.iconStroke} x="36" y="26" width="6" height="18" rx="1" />
            </svg>

            <svg className={iconClass(currentStep === 3)} viewBox="0 0 52 52" fill="none" aria-hidden>
              <circle cx="26" cy="26" r="5" fill="rgba(0,232,123,0.35)" />
              <circle className={styles.iconStroke} cx="26" cy="26" r="5" />
              <circle cx="10" cy="12" r="4" fill="rgba(0,232,123,0.2)" />
              <circle className={styles.iconStroke} cx="10" cy="12" r="4" />
              <circle cx="42" cy="12" r="4" fill="rgba(0,232,123,0.2)" />
              <circle className={styles.iconStroke} cx="42" cy="12" r="4" />
              <circle cx="10" cy="40" r="4" fill="rgba(0,232,123,0.2)" />
              <circle className={styles.iconStroke} cx="10" cy="40" r="4" />
              <circle cx="42" cy="40" r="4" fill="rgba(0,232,123,0.2)" />
              <circle className={styles.iconStroke} cx="42" cy="40" r="4" />
              <path className={styles.iconStroke} d="M14 15l9 9M38 15l-9 9M14 37l9-9M38 37l-9-9" />
              <path className={styles.iconStroke} d="M21 26H15M31 26h6M26 21v-6M26 31v6" />
            </svg>

            <svg className={iconClass(currentStep === 4)} viewBox="0 0 52 52" fill="none" aria-hidden>
              <path d="M8 44L20 28l8 8 8-16 8 12" fill="rgba(0,232,123,0.1)" />
              <path className={styles.iconStroke} d="M8 44L20 28l8 8 8-16 8 12" />
              <circle fill="var(--loader-green)" r="3" cx="8" cy="44" opacity="0.8" />
              <circle fill="var(--loader-green)" r="3" cx="20" cy="28" opacity="0.8" />
              <circle fill="var(--loader-green)" r="3" cx="28" cy="36" opacity="0.8" />
              <circle fill="var(--loader-green)" r="3" cx="36" cy="20" opacity="0.8" />
              <circle fill="var(--loader-green)" r="3" cx="44" cy="32" opacity="0.8" />
              <path className={styles.iconStroke} d="M8 10h36M8 18h20" opacity="0.4" />
            </svg>
          </div>
        </div>

        <div className={styles.brand}>GraphSentinel // System Init</div>

        <div className={styles.stepTitle}>
          {step.titlePrefix} <span className={styles.hl}>{step.titleHighlight}</span>
        </div>
        <div className={styles.stepSubtitle}>{step.subtitle}</div>

        <div className={styles.progressTrack}>
          <div className={styles.progressFill} style={{ width: `${step.progress}%` }} />
          <div className={styles.stepMarkers}>
            {markerIndexes.map((idx) => (
              <div
                key={idx}
                className={`${styles.stepDot} ${idx < currentStep ? styles.done : ''} ${idx === currentStep ? styles.active : ''}`}
              />
            ))}
          </div>
        </div>

        <div className={styles.points}>
          {step.points.map((point, idx) => {
            const phase = pointPhase[idx] ?? 'hidden';
            const phaseClass = phase === 'hidden' ? '' : phase === 'visible' ? styles.visible : `${styles.visible} ${styles.complete}`;
            const tagColor = pointColors[point.tag];

            return (
              <div key={`${point.text}-${idx}`} className={`${styles.point} ${phaseClass}`}>
                <div className={styles.pointBullet}>
                  <div className={styles.dot} />
                </div>
                <span className={styles.pointText}>{point.text}</span>
                <span
                  className={styles.pointTag}
                  style={{
                    color: tagColor,
                    borderColor: `${tagColor}30`,
                    background: `${tagColor}10`,
                  }}
                >
                  {point.tag}
                </span>
              </div>
            );
          })}
        </div>

        {/* <div className={styles.ticker}>
          <span className={styles.tickerInner}>{tickerText}   ·   {tickerText}</span>
        </div> */}
      </div>
    </div>
  );
}
