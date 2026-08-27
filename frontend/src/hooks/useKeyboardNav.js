import { useState, useEffect, useCallback, useRef } from 'react';

export default function useKeyboardNav(itemCount, colsPerRow, onSelect) {
  const [focusIndex, setFocusIndex] = useState(-1);
  const containerRef = useRef(null);

  const handleKeyDown = useCallback((e) => {
    if (itemCount === 0) return;

    const key = e.key;
    let next = focusIndex;

    switch (key) {
      case 'ArrowRight':
        e.preventDefault();
        next = Math.min(focusIndex + 1, itemCount - 1);
        break;
      case 'ArrowLeft':
        e.preventDefault();
        next = Math.max(focusIndex - 1, 0);
        break;
      case 'ArrowDown':
        e.preventDefault();
        next = Math.min(focusIndex + colsPerRow, itemCount - 1);
        break;
      case 'ArrowUp':
        e.preventDefault();
        next = Math.max(focusIndex - colsPerRow, 0);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (focusIndex >= 0 && onSelect) onSelect(focusIndex);
        return;
      case 'Escape':
        e.preventDefault();
        setFocusIndex(-1);
        return;
      case 'Home':
        e.preventDefault();
        next = 0;
        break;
      case 'End':
        e.preventDefault();
        next = itemCount - 1;
        break;
      default:
        return;
    }

    setFocusIndex(next);

    // Scroll focused item into view
    if (containerRef.current) {
      const cards = containerRef.current.querySelectorAll('[data-keyboard-card]');
      if (cards[next]) {
        cards[next].scrollIntoView({ block: 'nearest', inline: 'nearest' });
      }
    }
  }, [focusIndex, itemCount, colsPerRow, onSelect]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return { focusIndex, setFocusIndex, containerRef };
}
