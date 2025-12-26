'use client';

import { useState } from 'react';
import { generateImage, type ImageGenerationResponse } from '@/lib/api';
import toast from 'react-hot-toast';

interface ImageGeneratorProps {
  onImageGenerated?: (image: ImageGenerationResponse) => void;
}

export default function ImageGenerator({ onImageGenerated }: ImageGeneratorProps) {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<ImageGenerationResponse | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setIsGenerating(true);
    try {
      const result = await generateImage({ prompt: prompt.trim() });
      setGeneratedImage(result);

      // Notify parent component
      if (onImageGenerated) {
        onImageGenerated(result);
      }

      toast.success('Image generated successfully!');
    } catch (error) {
      console.error('Image generation failed:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to generate image');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClear = () => {
    setGeneratedImage(null);
    setPrompt('');
  };

  const handleDownload = () => {
    if (!generatedImage) return;

    // Create a download link
    const link = document.createElement('a');
    link.href = `data:${generatedImage.mime_type};base64,${generatedImage.image_data}`;
    link.download = `thesis-generated-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success('Image downloaded!');
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Image Generator
          </h2>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Powered by Nano Banana
          </span>
        </div>

        {/* Prompt Input */}
        <div className="space-y-2">
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Describe the image you want to generate
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., A futuristic classroom with AI assistants helping students learn..."
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none"
            rows={4}
            disabled={isGenerating}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Be specific and descriptive for best results
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors duration-200"
          >
            {isGenerating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </span>
            ) : (
              'Generate Image'
            )}
          </button>

          {generatedImage && (
            <button
              onClick={handleClear}
              className="px-6 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium rounded-lg transition-colors duration-200"
            >
              Clear
            </button>
          )}
        </div>

        {/* Generated Image Display */}
        {generatedImage && (
          <div className="space-y-3 mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Generated Image
              </p>
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors duration-200"
              >
                Download
              </button>
            </div>

            <div className="relative rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
              <img
                src={`data:${generatedImage.mime_type};base64,${generatedImage.image_data}`}
                alt={generatedImage.prompt}
                className="w-full h-auto"
              />
            </div>

            <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
              <p><strong>Prompt:</strong> {generatedImage.prompt}</p>
              <p><strong>Model:</strong> {generatedImage.model}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
