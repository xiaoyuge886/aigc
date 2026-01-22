/**
 * 日志工具类
 */
export class Logger {
  private static isDev = import.meta.env.DEV;
  private static apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  private static originalConsole: {
    log: typeof console.log;
    warn: typeof console.warn;
    error: typeof console.error;
    info: typeof console.info;
    debug: typeof console.debug;
  } | null = null;
  private static isIntercepted = false;
  
  /**
   * 发送日志到后端
   */
  private static async sendToBackend(level: string, message: string, data?: any) {
    try {
      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // 格式化消息，如果有 data 则合并
      let logMessage = message;
      if (data !== undefined && data !== null) {
        try {
          const dataStr = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
          logMessage = `${message}\n${dataStr}`;
        } catch (e) {
          logMessage = `${message}\n${String(data)}`;
        }
      }
      
      await fetch(`${this.apiBaseUrl}/api/v1/frontend/log`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          level: level,
          message: logMessage,
          data: data,
          timestamp: new Date().toISOString(),
          source: 'frontend'
        })
      });
    } catch (error) {
      // 静默失败，避免日志发送失败影响应用
      // 使用原始 console.error 避免循环
      if (this.originalConsole) {
        this.originalConsole.error('Failed to send log to backend:', error);
      }
    }
  }
  
  /**
   * 拦截 console 方法，将日志发送到后端
   * 注意：已禁用自动发送，只在显式调用 Logger 方法时发送
   */
  static interceptConsole() {
    if (this.isIntercepted) {
      return;
    }
    
    // 保存原始 console 方法
    this.originalConsole = {
      log: console.log.bind(console),
      warn: console.warn.bind(console),
      error: console.error.bind(console),
      info: console.info.bind(console),
      debug: console.debug.bind(console),
    };
    
    // 拦截 console.log - 不再自动发送到后端
    console.log = (...args: any[]) => {
      this.originalConsole!.log(...args);
      // 不再自动发送到后端，减少 API 调用
    };
    
    // 拦截 console.warn - 不再自动发送到后端
    console.warn = (...args: any[]) => {
      this.originalConsole!.warn(...args);
      // 不再自动发送到后端，减少 API 调用
    };
    
    // 拦截 console.error - 只在生产环境发送错误到后端
    console.error = (...args: any[]) => {
      this.originalConsole!.error(...args);
      // 只在生产环境且是真正的错误时发送
      if (!this.isDev) {
        const message = args.map(arg => 
          typeof arg === 'string' ? arg : JSON.stringify(arg, null, 2)
        ).join(' ');
        this.sendToBackend('error', message, args.length > 1 ? args.slice(1) : undefined);
      }
    };
    
    // 拦截 console.info - 不再自动发送到后端
    console.info = (...args: any[]) => {
      this.originalConsole!.info(...args);
      // 不再自动发送到后端，减少 API 调用
    };
    
    // 拦截 console.debug - 不再自动发送到后端
    console.debug = (...args: any[]) => {
      this.originalConsole!.debug(...args);
      // 不再自动发送到后端，减少 API 调用
    };
    
    this.isIntercepted = true;
  }
  
  /**
   * 恢复原始 console 方法
   */
  static restoreConsole() {
    if (!this.isIntercepted || !this.originalConsole) {
      return;
    }
    
    console.log = this.originalConsole.log;
    console.warn = this.originalConsole.warn;
    console.error = this.originalConsole.error;
    console.info = this.originalConsole.info;
    console.debug = this.originalConsole.debug;
    
    this.isIntercepted = false;
  }

  /**
   * 格式化时间戳
   */
  private static timestamp(): string {
    const now = new Date();
    return now.toISOString().replace('T', ' ').substring(0, 19);
  }

  /**
   * 格式化日志前缀
   */
  private static prefix(level: string, color: string): string {
    const timestamp = this.timestamp();
    const colors = {
      blue: '\x1b[34m',
      green: '\x1b[32m',
      yellow: '\x1b[33m',
      red: '\x1b[31m',
      reset: '\x1b[0m'
    };
    return `${colors.blue}[${timestamp}]${colors.reset} ${color}[${level}]${colors.reset}`;
  }

  /**
   * 信息日志
   */
  static info(message: string, data?: any) {
    if (this.isDev) {
      console.log(`${this.prefix('INFO', '\x1b[32m')} ${message}`, data || '');
    }
    // 不再自动发送到后端，减少 API 调用
    // this.sendToBackend('info', message, data);
  }

  /**
   * 警告日志
   */
  static warn(message: string, data?: any) {
    console.warn(`${this.prefix('WARN', '\x1b[33m')} ${message}`, data || '');
    // 不再自动发送到后端，减少 API 调用
    // this.sendToBackend('warn', message, data);
  }

  /**
   * 错误日志
   */
  static error(message: string, error?: any) {
    console.error(`${this.prefix('ERROR', '\x1b[31m')} ${message}`, error || '');
    // 只在生产环境发送错误到后端
    if (!this.isDev) {
      this.sendToBackend('error', message, error);
    }
  }

  /**
   * 请求日志
   */
  static request(method: string, url: string, data?: any) {
    if (this.isDev) {
      const logMsg = `${this.prefix('REQ', '\x1b[34m')} ${method} ${url}`;
      if (data) {
        console.log(logMsg, '\n  → 请求参数:', data);
      } else {
        console.log(logMsg);
      }
    }
  }

  /**
   * 响应日志
   */
  static response(url: string, status: number, data?: any) {
    if (this.isDev) {
      const color = status >= 200 && status < 300 ? '\x1b[32m' : '\x1b[31m';
      const logMsg = `${this.prefix('RES', color)} ${url} (${status})`;
      if (data) {
        console.log(logMsg, '\n  ← 响应数据:', data);
      } else {
        console.log(logMsg);
      }
    }
  }

  /**
   * 流式数据日志
   */
  static stream(chunk: string, index: number) {
    if (this.isDev && index % 50 === 0) { // 每50个chunk输出一次
      console.log(`${this.prefix('STREAM', '\x1b[36m')} Chunk #${index} (${chunk.length} chars)`);
    }
  }

  /**
   * 分组日志开始
   */
  static group(label: string) {
    if (this.isDev) {
      console.group(`${this.prefix('GROUP', '\x1b[35m')} ${label}`);
    }
  }

  /**
   * 分组日志结束
   */
  static groupEnd() {
    if (this.isDev) {
      console.groupEnd();
    }
  }

  /**
   * 表格日志
   */
  static table(data: any[]) {
    if (this.isDev) {
      console.table(data);
    }
  }
}

/**
 * 性能监控工具
 */
export class PerformanceLogger {
  private static timers = new Map<string, number>();

  /**
   * 开始计时
   */
  static start(label: string) {
    this.timers.set(label, performance.now());
    Logger.info(`⏱️  开始计时: ${label}`);
  }

  /**
   * 结束计时
   */
  static end(label: string) {
    const startTime = this.timers.get(label);
    if (startTime) {
      const duration = performance.now() - startTime;
      this.timers.delete(label);
      Logger.info(`⏱️  计时结束: ${label} (${duration.toFixed(2)}ms)`);
      return duration;
    } else {
      Logger.warn(`计时器不存在: ${label}`);
      return 0;
    }
  }
}
