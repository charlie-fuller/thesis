import React from 'react';

interface MarkdownTextProps {
  content: string;
  className?: string;
}

/**
 * Simple markdown renderer for help chat messages.
 * Supports:
 * - **bold text**
 * - Line breaks
 * - Lists (- item)
 */
export default function MarkdownText({ content, className = '' }: MarkdownTextProps) {
  // Split by lines to handle lists and paragraphs
  const lines = content.split('\n');

  const renderLine = (line: string, index: number) => {
    // Check if it's a list item
    const listMatch = line.match(/^[-*]\s+(.+)$/);
    if (listMatch) {
      return (
        <li key={index} className="ml-4">
          {renderInlineFormatting(listMatch[1])}
        </li>
      );
    }

    // Regular paragraph
    if (line.trim()) {
      return (
        <p key={index} className="mb-2 last:mb-0">
          {renderInlineFormatting(line)}
        </p>
      );
    }

    // Empty line
    return <br key={index} />;
  };

  const renderInlineFormatting = (text: string) => {
    // Split by ** to find bold sections (non-greedy match)
    const parts = text.split(/(\*\*.*?\*\*)/g);

    return parts.map((part, i) => {
      // Check if this part is bold (surrounded by **)
      const boldMatch = part.match(/^\*\*(.*?)\*\*$/);
      if (boldMatch) {
        return <strong key={i} className="font-semibold">{boldMatch[1]}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  // Group consecutive list items
  const groupedElements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];

  lines.forEach((line, index) => {
    const listMatch = line.match(/^[-*]\s+(.+)$/);

    if (listMatch) {
      currentList.push(
        <li key={index} className="ml-4">
          {renderInlineFormatting(listMatch[1])}
        </li>
      );
    } else {
      // If we have accumulated list items, add them as a ul
      if (currentList.length > 0) {
        groupedElements.push(
          <ul key={`list-${index}`} className="list-disc mb-2">
            {currentList}
          </ul>
        );
        currentList = [];
      }

      // Add the non-list line
      if (line.trim()) {
        groupedElements.push(
          <p key={index} className="mb-2 last:mb-0">
            {renderInlineFormatting(line)}
          </p>
        );
      } else {
        groupedElements.push(<br key={index} />);
      }
    }
  });

  // Don't forget remaining list items
  if (currentList.length > 0) {
    groupedElements.push(
      <ul key="list-final" className="list-disc mb-2">
        {currentList}
      </ul>
    );
  }

  return <div className={className}>{groupedElements}</div>;
}
