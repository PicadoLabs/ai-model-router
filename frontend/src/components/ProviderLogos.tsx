import React from 'react';

interface LogoProps {
  className?: string;
}

export const OpenAILogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9013 6.066 6.066 0 0 0-4.939-2.0089 6.0505 6.0505 0 0 0-5.833 4.2383 6.0474 6.0474 0 0 0-4.0044 2.9014 6.0072 6.0072 0 0 0 .7087 7.0267 5.984 5.984 0 0 0 .5156 4.9108 6.0461 6.0461 0 0 0 6.5097 2.9013 6.0659 6.0659 0 0 0 4.9391 2.0089 6.0505 6.0505 0 0 0 5.833-4.2383 6.0474 6.0474 0 0 0 4.0044-2.9014 6.007 6.007 0 0 0-.7087-7.0267zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0813 4.779-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.5045 4.5045 0 0 1-4.4952 4.4953zm-8.86-4.5714a4.4737 4.4737 0 0 1-.535-3.0037l.142.0831 4.779 2.7583a.7948.7948 0 0 0 .7927 0l5.8346-3.3703v2.3372a.071.071 0 0 1-.0232.0607l-4.8345 2.7913a4.5044 4.5044 0 0 1-6.1556-1.6566zm-1.2984-9.9715a4.4737 4.4737 0 0 1 2.3415-1.9628l-.0001.1643v5.5164a.7948.7948 0 0 0 .4 0l5.8346-3.3703-2.02-1.1686a.071.071 0 0 1-.038-.052v-5.5826a4.5044 4.5044 0 0 1 6.1556 1.6566c.159.2754.2882.5684.386.8727l-.142-.0831-4.779-2.7583a.7948.7948 0 0 0-.7927 0l-5.8346 3.3703v-2.3372a.071.071 0 0 1 .0232-.0607l4.8345-2.7913a4.5044 4.5044 0 0 1 6.1556 1.6566z" />
  </svg>
);

export const AnthropicLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.414 4.5h-3.554l-5.717 15h3.554l1.173-3.153h5.88l1.173 3.153h3.554l-5.717-15zm-3.36 9.176l2.128-5.718 2.128 5.718h-4.256zM2.846 4.5H.154l5.717 15h3.554L3.708 4.5z" />
  </svg>
);

export const GeminiLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C12 6.62742 6.62742 12 0 12C6.62742 12 12 17.3726 12 24C12 17.3726 17.3726 12 24 12C17.3726 12 12 6.62742 12 0Z" />
  </svg>
);

export const DeepSeekLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14.5h-2v-2h2v2zm0-4h-2V7h2v5.5z" />
  </svg>
);

export const GroqLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M13 2L3 14h7v8l10-12h-7V2z" />
  </svg>
);

export const OllamaLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-6h2zm0-8h-2V7h2z" />
  </svg>
);

export const LangChainLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M7 7h10v2H7zm0 4h10v2H7zm0 4h7v2H7z" />
  </svg>
);

export const LlamaIndexLogo: React.FC<LogoProps> = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M4 4h16v16H4V4zm2 2v12h12V6H6z" />
  </svg>
);

export const ProviderIconMap: Record<string, React.FC<LogoProps>> = {
  'OpenAI': OpenAILogo,
  'Anthropic': AnthropicLogo,
  'Google Gemini': GeminiLogo,
  'DeepSeek': DeepSeekLogo,
  'Groq': GroqLogo,
  'Ollama': OllamaLogo,
  'LangChain': LangChainLogo,
  'LlamaIndex': LlamaIndexLogo,
};
