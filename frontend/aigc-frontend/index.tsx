import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import * as d3 from 'd3';
import { Markmap, loadCSS, loadJS } from 'markmap-view';
import { Transformer } from 'markmap-lib';
import { Logger } from './utils/logger';

// 拦截 console 方法，将日志发送到后端
Logger.interceptConsole();

// Mount to window for components that expect global markmap
(window as any).d3 = d3;
(window as any).markmap = {
  Markmap,
  Transformer,
  loadCSS,
  loadJS
};

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);

root.render(
  <App />
);