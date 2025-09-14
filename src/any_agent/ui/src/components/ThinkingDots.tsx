import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';

interface ThinkingVariation {
  emojis: string[];
  text: string;
  color?: string;
  animationSpeed?: number;
}

const THINKING_VARIATIONS: ThinkingVariation[] = [
  // 1. Progressive sequence: thinking face → lightbulb moment → sparkles
  {
    emojis: ['🤔', '💡', '✨'],
    text: 'Processing...',
    color: '#FFA726', // warm orange
    animationSpeed: 2000
  },
  
  // 2. Brain with lightning bolt - neural network energy
  {
    emojis: ['🧠', '⚡'],
    text: 'Thinking deeply...',
    color: '#42A5F5', // electric blue
    animationSpeed: 1200
  },
  
  // 3. Detective mode: magnifying glass + sleuth
  {
    emojis: ['🔍', '🕵️‍♀️'],
    text: 'Investigating...',
    color: '#66BB6A', // detective green
    animationSpeed: 1600
  },
  
  // 4. Knowledge gathering: books → pages → writing
  {
    emojis: ['📚', '📖', '📝'],
    text: 'Gathering knowledge...',
    color: '#8D6E63', // book brown
    animationSpeed: 1800
  },
  
  // 5. Building response: gears and tools
  {
    emojis: ['⚙️', '🔧', '🛠️'],
    text: 'Crafting response...',
    color: '#78909C', // metallic gray
    animationSpeed: 1400
  },
  
  // 6. Robot building energy to starburst
  {
    emojis: ['🤖', '⚡', '💫'],
    text: 'Computing magic...',
    color: '#AB47BC', // tech purple
    animationSpeed: 1300
  }
];

const ThinkingDots: React.FC = () => {
  const [variation] = useState(() => 
    THINKING_VARIATIONS[Math.floor(Math.random() * THINKING_VARIATIONS.length)]
  );
  const [currentEmojiIndex, setCurrentEmojiIndex] = useState(0);

  // Cycle through emojis for the selected variation
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentEmojiIndex((prev) => (prev + 1) % variation.emojis.length);
    }, variation.animationSpeed || 1500);

    return () => clearInterval(interval);
  }, [variation]);

  return (
    <Box
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 1,
        py: 0.5,
      }}
    >
      {/* Animated emoji sequence */}
      <Box
        component="span"
        sx={{
          fontSize: '1.1rem',
          mr: 0.5,
          transition: 'all 0.3s ease-in-out',
          transform: 'scale(1)',
          animation: 'emojiPulse 0.6s ease-in-out infinite alternate',
          '@keyframes emojiPulse': {
            '0%': { transform: 'scale(1)' },
            '100%': { transform: 'scale(1.1)' }
          }
        }}
      >
        {variation.emojis[currentEmojiIndex]}
      </Box>

      {/* Thinking text */}
      <Typography
        variant="caption"
        sx={{
          fontSize: '0.75rem',
          color: variation.color || 'text.secondary',
          fontStyle: 'italic',
          mr: 1,
          minWidth: '80px',
          opacity: 0.8
        }}
      >
        {variation.text}
      </Typography>

      {/* Animated dots */}
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.25,
        }}
      >
        {[0, 1, 2].map((i) => (
          <Box
            key={i}
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: variation.color || 'text.secondary',
              animation: 'thinkingDots 1.4s ease-in-out infinite both',
              animationDelay: `${i * 0.16}s`,
              '@keyframes thinkingDots': {
                '0%, 80%, 100%': {
                  transform: 'scale(0)',
                  opacity: 0.5,
                },
                '40%': {
                  transform: 'scale(1)',
                  opacity: 1,
                },
              },
            }}
          />
        ))}
      </Box>
    </Box>
  );
};

export default ThinkingDots;