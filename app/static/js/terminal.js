(function () {
  const BOOT_DONE = 2.2 + 0.22;
  const screen    = document.getElementById('screen');
  const inputLine = document.getElementById('input-line');
  const inputText = document.getElementById('input-text');
  const promptEl  = inputLine.querySelector('.appPrompt');

  // ── Session state ────────────────────────────────────────────
  const SESSION_ID = crypto.randomUUID();
  let cwd    = '~';
  let mode   = 'portfolio';
  let buffer = '';

  // ── Prompt ───────────────────────────────────────────────────
  function updatePrompt() {
    promptEl.textContent = `portfolio:${cwd}$`;
  }

  // ── Tab completion ───────────────────────────────────────────
  let COMMAND_NAMES = [];
  let fsTree        = {};

  async function loadCommands() {
    try {
      const res  = await fetch('/api/commands');
      const data = await res.json();
      COMMAND_NAMES = Object.keys(data);
    } catch (e) {
      console.warn('Could not load commands:', e);
    }
  }

  async function loadFsTree() {
    try {
      const res  = await fetch('/api/filesystem');
      const data = await res.json();
      fsTree = {};
      for (const [path, children] of Object.entries(data)) {
        fsTree[path] = {
          dirs:  children.filter(c => typeof c === 'string'),
          files: children.filter(c => typeof c === 'object').map(c => c.name),
        };
      }
    } catch (e) {
      console.warn('Could not load filesystem:', e);
    }
  }

  function tabComplete(buf) {
    const parts = buf.split(/\s+/);

    if (parts.length === 1) {
      const partial = parts[0];
      const matches = COMMAND_NAMES.filter(c => c.startsWith(partial));
      if (matches.length === 1) return matches[0];
      if (matches.length > 1) {
        printSpacer();
        print([matches.join('   ')]);
        printSpacer();
        screen.scrollTop = screen.scrollHeight;
      }
      return buf;
    }

    const cmd     = parts[0].toLowerCase();
    const partial = parts[parts.length - 1].replace(/\/$/, '');
    const node    = fsTree[cwd] || { dirs: [], files: [] };

    let candidates = [];
    if (cmd === 'cd')        candidates = node.dirs;
    else if (cmd === 'view') candidates = node.files;
    else                     candidates = [...node.dirs, ...node.files];

    const matches = candidates.filter(n => n.startsWith(partial));

    if (matches.length === 1) {
      const isDir = node.dirs.includes(matches[0]);
      parts[parts.length - 1] = matches[0] + (isDir ? '/' : '');
      return parts.join(' ');
    }
    if (matches.length > 1) {
      printSpacer();
      print([matches.map(m => node.dirs.includes(m)
        ? `<span class="accent2">${m}/</span>`
        : m
      ).join('   ')]);
      printSpacer();
      screen.scrollTop = screen.scrollHeight;
    }
    return buf;
  }

  // ── Output helpers ───────────────────────────────────────────
  const TYPE_CLASS = { ok: 'ok', error: 'error', info: 'muted', text: '' };

  function print(lines, isError = false) {
    lines.forEach(html => {
      const div = document.createElement('div');
      div.className = 'line output' + (isError ? ' error' : '');
      div.innerHTML = html;
      screen.insertBefore(div, inputLine);
    });
  }

  function printLines(terminalLines) {
    terminalLines.forEach(({ type, content, html }) => {
      const div = document.createElement('div');
      const cls = TYPE_CLASS[type] || '';
      div.className = 'line output' + (cls ? ' ' + cls : '');
      if (html) {
        div.innerHTML = content;
      } else {
        div.textContent = content;
      }
      screen.insertBefore(div, inputLine);
    });
  }

  function printSpacer() {
    const div = document.createElement('div');
    div.className = 'spacer';
    screen.insertBefore(div, inputLine);
  }

  function echoCommand(cmd) {
    const div = document.createElement('div');
    div.className = 'line output';
    div.innerHTML = `<span class="appPrompt">portfolio:${cwd}$</span>&nbsp;${cmd}`;
    screen.insertBefore(div, inputLine);
  }

  // ── Right pane ───────────────────────────────────────────────
  function openPdf(url) {
    const filename = url.split('/').pop();
    document.getElementById('pdf-title').textContent = filename;
    document.getElementById('pdf-viewer').innerHTML  = `<iframe src="${url}#toolbar=0" style="width:100%;height:100%;border:none;"></iframe>`;
    document.querySelector('.workspace').classList.add('split');
  }

  function openReadme(projectName) {
    const title  = document.getElementById('pdf-title');
    const viewer = document.getElementById('pdf-viewer');

    title.innerHTML = `${projectName} / README.md`;
    viewer.innerHTML = `
      <div class="pdf-loading">
        <div class="pdf-loading__spinner"></div>
        <span>fetching README…</span>
      </div>`;
    document.querySelector('.workspace').classList.add('split');

    fetch(`/api/projects/${projectName}/readme`)
      .then(r => r.json())
      .then(data => {
        if (data.github_url) {
          title.innerHTML = `${projectName} / README.md &nbsp;<a href="${data.github_url}" target="_blank" class="muted" style="font-size:11px;text-decoration:none;opacity:0.6;">↗ github</a>`;
        }
        viewer.innerHTML = `<div class="readme-body">${data.html}</div>`;
      })
      .catch(() => {
        viewer.innerHTML = `<div class="pdf-loading"><span class="muted">failed to load README</span></div>`;
      });
  }

  // ── API call ─────────────────────────────────────────────────
  async function sendCommand(raw) {
    const res = await fetch('/api/command', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: SESSION_ID, mode, cwd, command: raw.trim() }),
    });
    if (!res.ok) return null;
    return res.json();
  }

  // ── Command runner ───────────────────────────────────────────
  async function runCommand(raw) {
    const trimmed = raw.trim();
    if (!trimmed) return;

    if (trimmed === 'clear') {
      Array.from(screen.children).forEach(el => {
        if (el !== inputLine) el.remove();
      });
      return;
    }

    if (trimmed.startsWith('cd')) {
      const target = trimmed.split(/\s+/)[1];
      echoCommand(trimmed);
      printSpacer();
      handleCd(target);
      printSpacer();
      screen.scrollTop = screen.scrollHeight;
      return;
    }

    echoCommand(trimmed);
    printSpacer();

    const data = await sendCommand(trimmed);

    if (!data) {
      print(['<span class="error">error: could not reach server</span>']);
    } else {
      if (data.cwd  != null) { cwd  = data.cwd;  updatePrompt(); }
      if (data.mode != null) { mode = data.mode; }
      if (data.lines && data.lines.length) printLines(data.lines);

      if (data.open_url) {
        if (data.open_url.endsWith('.pdf') || data.open_url.includes('resume')) {
          openPdf(data.open_url);
        } else {
          window.open(data.open_url, '_blank');
        }
      }

      if (data.open_readme) {
        openReadme(data.open_readme);
      }
    }

    printSpacer();
    screen.scrollTop = screen.scrollHeight;
  }

  // ── CD handler (client-side) ─────────────────────────────────
  function handleCd(target) {
    if (!target || target === '~') {
      cwd = '~';
    } else if (target === '..') {
      if (cwd !== '~') cwd = cwd.split('/').slice(0, -1).join('/') || '~';
    } else {
      const name = target.replace(/\/$/, '');
      const node = fsTree[cwd] || { dirs: [] };
      if (node.dirs.includes(name)) {
        cwd = cwd === '~' ? `~/${name}` : `${cwd}/${name}`;
      } else {
        print([`<span class="error">cd: ${name}: No such file or directory</span>`]);
        return;
      }
    }
    updatePrompt();
  }

  // ── Boot then activate ───────────────────────────────────────
  updatePrompt();

  setTimeout(async () => {
    await Promise.all([loadCommands(), loadFsTree()]);
    inputLine.classList.add('ready');

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        buffer = tabComplete(buffer);
        inputText.textContent = buffer;
      } else if (e.key === 'Enter') {
        const cmd = buffer;
        buffer = '';
        inputText.textContent = '';
        runCommand(cmd);
      } else if (e.key === 'Backspace') {
        buffer = buffer.slice(0, -1);
        inputText.textContent = buffer;
      } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
        buffer += e.key;
        inputText.textContent = buffer;
      }
    });
  }, BOOT_DONE * 1000);
})();