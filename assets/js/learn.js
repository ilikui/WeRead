(function () {
    const root = document.getElementById('learnPage');
    if (!root) return;

    const gistUrl = root.dataset.gistUrl;
    const commentsUrl = root.dataset.commentsUrl;
    const gistId = gistUrl.split('/').filter(Boolean).pop();
    const gistApiUrl = `https://api.github.com/gists/${gistId}`;
    const preferredFilename = '2026-11-06.md';
    const files = [];
    let calendarMonth = null;
    let activeFilename = '';

    const byId = (id) => document.getElementById(id);

    function dateFromFilename(filename) {
        const match = filename.match(/^(\d{4})-(\d{2})-(\d{2})\.md$/i);
        if (!match) return null;
        const [, year, month, day] = match;
        const date = new Date(Number(year), Number(month) - 1, Number(day));
        return date.getFullYear() === Number(year) && date.getMonth() === Number(month) - 1 && date.getDate() === Number(day)
            ? date
            : null;
    }

    function titleFor(file) {
        const heading = file.content.match(/^#\s+(.+)$/m);
        const headingText = heading?.[1].replace(/^📆\s*\d{4}-\d{2}-\d{2}\s*/, '').trim();
        const subheading = file.content.match(/^#{2,3}\s+(.+)$/m);
        return headingText || subheading?.[1].trim() || file.filename;
    }

    function renderMarkdown(markdown) {
        const source = String(markdown || '').replace(/\\([()[\]])/g, (_, delimiter) => `\\\\${delimiter}`);
        const html = marked.parse(source, { gfm: true, breaks: false });
        return DOMPurify.sanitize(html);
    }

    async function renderMarkdownInto(container, markdown) {
        container.innerHTML = renderMarkdown(markdown);
        container.querySelectorAll('pre > code.language-mermaid').forEach(code => {
            const diagram = document.createElement('pre');
            diagram.className = 'mermaid';
            diagram.textContent = code.textContent;
            code.parentElement.replaceWith(diagram);
        });
        renderMathInElement(container, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '\\[', right: '\\]', display: true },
                { left: '\\begin{equation}', right: '\\end{equation}', display: true },
                { left: '\\begin{equation*}', right: '\\end{equation*}', display: true },
                { left: '\\begin{align}', right: '\\end{align}', display: true },
                { left: '\\begin{align*}', right: '\\end{align*}', display: true },
                { left: '\\begin{gather}', right: '\\end{gather}', display: true },
                { left: '\\begin{gather*}', right: '\\end{gather*}', display: true },
                { left: '\\(', right: '\\)', display: false },
                { left: '$', right: '$', display: false }
            ],
            throwOnError: false
        });
        try {
            await mermaid.run({ nodes: container.querySelectorAll('.mermaid') });
        } catch (error) {
            console.error('Learn Mermaid rendering failed', error);
        }
    }

    function updateView(view) {
        const isCalendar = view === 'calendar';
        byId('learnNotesTab').setAttribute('aria-selected', String(!isCalendar));
        byId('learnCalendarTab').setAttribute('aria-selected', String(isCalendar));
        byId('learnCalendar').hidden = !isCalendar;
        byId('learnArticle').hidden = isCalendar || !activeFilename;
        byId('learnComments').hidden = isCalendar || !activeFilename;
        if (isCalendar) renderCalendar();
    }

    function setView(view) {
        const isCalendar = view === 'calendar';
        byId('learnNotesTab').setAttribute('aria-selected', String(!isCalendar));
        byId('learnCalendarTab').setAttribute('aria-selected', String(isCalendar));
        byId('learnCalendar').hidden = !isCalendar;
        byId('learnArticle').hidden = isCalendar || !activeFilename;
        byId('learnComments').hidden = isCalendar || !activeFilename;
        if (isCalendar) renderCalendar();
    }

    function createTreeNote(file) {
        const date = dateFromFilename(file.filename);
        const button = document.createElement('button');
        button.className = 'learn-tree-note';
        button.type = 'button';
        button.setAttribute('role', 'treeitem');
        if (file.filename === activeFilename) button.setAttribute('aria-current', 'page');

        const dateLabel = document.createElement('span');
        dateLabel.className = 'learn-tree-note-date';
        dateLabel.textContent = date
            ? `${String(date.getMonth() + 1).padStart(2, '0')}月${String(date.getDate()).padStart(2, '0')}日`
            : file.filename;
        const title = document.createElement('span');
        title.className = 'learn-tree-note-title';
        title.textContent = titleFor(file);
        button.append(dateLabel, title);
        button.addEventListener('click', () => {
            renderNote(file.filename);
            byId('learnTreePanel').classList.remove('is-open');
            byId('learnSidebarToggle').setAttribute('aria-expanded', 'false');
        });
        return button;
    }

    function renderTree() {
        const tree = byId('learnTree');
        const dated = new Map();
        const undated = [];

        files.forEach(file => {
            const date = dateFromFilename(file.filename);
            if (!date) {
                undated.push(file);
                return;
            }
            const year = date.getFullYear();
            const entries = dated.get(year) || [];
            entries.push(file);
            dated.set(year, entries);
        });

        const selectedDate = dateFromFilename(activeFilename);
        const newestYear = dated.keys().next().value;
        const expandedYear = selectedDate?.getFullYear() ?? newestYear;
        const fragment = document.createDocumentFragment();

        [...dated.entries()].sort((a, b) => b[0] - a[0]).forEach(([year, entries]) => {
            const group = document.createElement('section');
            group.className = 'learn-tree-year';
            const toggle = document.createElement('button');
            toggle.className = 'learn-tree-year-toggle';
            toggle.type = 'button';
            const expanded = year === expandedYear;
            toggle.setAttribute('aria-expanded', String(expanded));

            const chevron = document.createElement('span');
            chevron.className = 'learn-tree-chevron';
            chevron.setAttribute('aria-hidden', 'true');
            chevron.textContent = '▶';
            const label = document.createElement('span');
            label.textContent = String(year);
            const count = document.createElement('span');
            count.className = 'learn-tree-count';
            count.textContent = `${entries.length} 篇`;
            toggle.append(chevron, label, count);

            const children = document.createElement('div');
            children.className = 'learn-tree-children';
            children.setAttribute('role', 'group');
            children.hidden = !expanded;
            entries.forEach(file => children.append(createTreeNote(file)));
            toggle.addEventListener('click', () => {
                const open = toggle.getAttribute('aria-expanded') === 'true';
                toggle.setAttribute('aria-expanded', String(!open));
                children.hidden = open;
            });
            group.append(toggle, children);
            fragment.append(group);
        });

        if (undated.length) {
            const group = document.createElement('section');
            group.className = 'learn-tree-year';
            const toggle = document.createElement('button');
            toggle.className = 'learn-tree-year-toggle';
            toggle.type = 'button';
            toggle.setAttribute('aria-expanded', 'true');
            const chevron = document.createElement('span');
            chevron.className = 'learn-tree-chevron';
            chevron.setAttribute('aria-hidden', 'true');
            chevron.textContent = '▶';
            const label = document.createElement('span');
            label.textContent = '未归档';
            const count = document.createElement('span');
            count.className = 'learn-tree-count';
            count.textContent = `${undated.length} 篇`;
            toggle.append(chevron, label, count);

            const children = document.createElement('div');
            children.className = 'learn-tree-children';
            children.setAttribute('role', 'group');
            undated.forEach(file => children.append(createTreeNote(file)));
            toggle.addEventListener('click', () => {
                const open = toggle.getAttribute('aria-expanded') === 'true';
                toggle.setAttribute('aria-expanded', String(!open));
                children.hidden = open;
            });
            group.append(toggle, children);
            fragment.append(group);
        }

        tree.replaceChildren(fragment);
        byId('learnNoteCount').textContent = String(files.length);
    }

    function renderCalendar() {
        if (!calendarMonth) return;
        const year = calendarMonth.getFullYear();
        const month = calendarMonth.getMonth();
        const first = new Date(year, month, 1);
        const dayCount = new Date(year, month + 1, 0).getDate();
        const offset = (first.getDay() + 6) % 7;
        const notesByDay = new Map();

        files.forEach(file => {
            const date = dateFromFilename(file.filename);
            if (!date || date.getFullYear() !== year || date.getMonth() !== month) return;
            const entries = notesByDay.get(date.getDate()) || [];
            entries.push(file);
            notesByDay.set(date.getDate(), entries);
        });

        byId('learnMonthTitle').textContent = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' }).format(first);
        const grid = byId('learnCalendarGrid');
        grid.replaceChildren();
        ['一', '二', '三', '四', '五', '六', '日'].forEach(day => {
            const label = document.createElement('span');
            label.className = 'learn-weekday';
            label.setAttribute('role', 'columnheader');
            label.textContent = day;
            grid.append(label);
        });
        for (let index = 0; index < offset; index += 1) {
            const blank = document.createElement('span');
            blank.className = 'learn-calendar-day';
            blank.setAttribute('aria-hidden', 'true');
            grid.append(blank);
        }
        for (let day = 1; day <= dayCount; day += 1) {
            const entries = notesByDay.get(day) || [];
            const cell = document.createElement(entries.length ? 'button' : 'span');
            cell.className = `learn-calendar-day${entries.length ? ' has-note' : ''}`;
            cell.textContent = String(day);
            if (entries.length) {
                cell.type = 'button';
                cell.setAttribute('aria-label', `${year}年${month + 1}月${day}日，有 ${entries.length} 篇笔记`);
                if (entries.some(file => file.filename === activeFilename)) cell.classList.add('is-selected');
                const dot = document.createElement('span');
                dot.className = 'learn-calendar-dot';
                dot.setAttribute('aria-hidden', 'true');
                cell.append(dot);
                cell.addEventListener('click', () => renderNote(entries[0].filename));
            }
            grid.append(cell);
        }
        const count = [...notesByDay.values()].reduce((sum, entries) => sum + entries.length, 0);
        byId('learnCalendarSummary').textContent = `${count} 篇笔记 · 点击日期打开`;
    }

    async function renderNote(filename) {
        const file = files.find(item => item.filename === filename);
        if (!file) return;
        activeFilename = file.filename;
        renderTree();
        const date = dateFromFilename(file.filename);
        if (date) calendarMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        byId('learnNoteTitle').textContent = titleFor(file);
        byId('learnNoteMeta').textContent = date ? `${date.toLocaleDateString('zh-CN')} · ${file.filename}` : file.filename;

        const body = byId('learnNoteBody');
        byId('learnLoading').hidden = true;
        byId('learnError').hidden = true;
        updateView('notes');
        await new Promise(resolve => requestAnimationFrame(resolve));
        await renderMarkdownInto(body, file.content);
    }

    async function loadNotes() {
        try {
            const response = await fetch(gistApiUrl, { headers: { Accept: 'application/vnd.github+json' } });
            if (!response.ok) throw new Error(`GitHub 返回了 ${response.status} 状态码`);
            const gist = await response.json();
            const markdownFiles = Object.values(gist.files || {}).filter(file => file.filename.toLowerCase().endsWith('.md'));
            const loadedFiles = await Promise.all(markdownFiles.map(async file => {
                if (file.truncated && file.raw_url) {
                    const rawResponse = await fetch(file.raw_url);
                    if (!rawResponse.ok) throw new Error(`${file.filename} 下载失败`);
                    file.content = await rawResponse.text();
                }
                return file;
            }));
            loadedFiles.sort((a, b) => b.filename.localeCompare(a.filename, undefined, { numeric: true }));
            if (!loadedFiles.length) throw new Error('Gist 中没有 Markdown 笔记');
            files.push(...loadedFiles);

            const preferred = loadedFiles.some(file => file.filename === preferredFilename) ? preferredFilename : loadedFiles[0].filename;
            const initialDate = dateFromFilename(preferred) || loadedFiles.map(file => dateFromFilename(file.filename)).find(Boolean) || new Date();
            calendarMonth = new Date(initialDate.getFullYear(), initialDate.getMonth(), 1);
            byId('learnGistLink').href = gist.html_url || gistUrl;
            await renderNote(preferred);
        } catch (error) {
            byId('learnLoading').hidden = true;
            byId('learnErrorMessage').textContent = `笔记加载失败：${error.message}`;
            byId('learnError').hidden = false;
        }
    }

    function renderComments(comments) {
        const sorted = comments.slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        const list = byId('learnCommentsList');
        byId('learnCommentsCount').textContent = `${sorted.length} 条`;
        byId('learnCommentsStatus').textContent = sorted.length ? '' : 'Gist 暂无评论。';
        list.replaceChildren();

        sorted.forEach(comment => {
            const details = document.createElement('details');
            details.className = 'learn-comment';
            const summary = document.createElement('summary');
            const title = document.createElement('span');
            title.className = 'learn-comment-title';
            const body = String(comment.body || '').trim();
            const heading = body.match(/^#{1,6}\s+(.+)$/m);
            const firstLine = body.split(/\r?\n/).find(line => line.trim()) || '';
            title.textContent = (heading?.[1] || firstLine.replace(/^>\s*/, '')).trim().slice(0, 120) || '无标题评论';

            const meta = document.createElement('span');
            meta.className = 'learn-comment-meta';
            const author = document.createElement('span');
            author.textContent = comment.user?.login || 'GitHub 用户';
            const time = document.createElement('time');
            if (comment.created_at) {
                time.dateTime = comment.created_at;
                time.textContent = new Date(comment.created_at).toLocaleString('zh-CN');
            }
            meta.append(author, time);
            summary.append(title, meta);

            const content = document.createElement('div');
            content.className = 'learn-comment-body';
            details.addEventListener('toggle', () => {
                if (details.open && !content.dataset.rendered) {
                    content.dataset.rendered = 'true';
                    renderMarkdownInto(content, comment.body || '');
                }
            });
            details.append(summary, content);
            list.append(details);
        });
    }

    async function loadComments() {
        byId('learnCommentsRetry').hidden = true;
        byId('learnCommentsStatus').textContent = '正在加载 Gist 评论…';
        try {
            const response = await fetch(`${commentsUrl}?per_page=100`, { headers: { Accept: 'application/vnd.github+json' } });
            if (!response.ok) throw new Error(`GitHub 返回了 ${response.status} 状态码`);
            const comments = await response.json();
            renderComments(Array.isArray(comments) ? comments : []);
        } catch (error) {
            byId('learnCommentsStatus').textContent = `评论加载失败：${error.message}`;
            byId('learnCommentsRetry').hidden = false;
        }
    }

    mermaid.initialize({
        startOnLoad: false,
        theme: 'base',
        securityLevel: 'strict',
        themeVariables: {
            cScale0: '#e5f3ff', cScaleLabel0: '#1f4d75',
            cScale1: '#e4f5ea', cScaleLabel1: '#245c3b',
            cScale2: '#fff0d4', cScaleLabel2: '#754b0b',
            cScale3: '#fce4e4', cScaleLabel3: '#7c3030',
            cScale4: '#eee7fa', cScaleLabel4: '#514071',
            cScale5: '#ddf3f2', cScaleLabel5: '#1e5c59',
            cScale6: '#f9e7d8', cScaleLabel6: '#73401f',
            cScale7: '#f1f3d9', cScaleLabel7: '#545a22',
            cScale8: '#e6e9fc', cScaleLabel8: '#374275',
            cScale9: '#f6e5f2', cScaleLabel9: '#6c315d',
            cScale10: '#e2edf0', cScaleLabel10: '#31515a',
            cScale11: '#f9edd8', cScaleLabel11: '#69501f'
        }
    });
    const renderer = new marked.Renderer();
    const renderBlockquote = marked.Renderer.prototype.blockquote;
    renderer.blockquote = function (token) {
        const content = token.raw.replace(/^>[ \t]?/gm, '');
        const match = content.match(/^\[!([\w-]+)\](?:[ \t]+([^\r\n]*))?(?:\r?\n|$)([\s\S]*)$/i);
        if (!match) return renderBlockquote.call(this, token);

        const type = match[1].toLowerCase();
        const title = match[2]?.trim() || `${match[1][0].toUpperCase()}${match[1].slice(1).toLowerCase()}`;
        const safeTitle = title.replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);
        const body = marked.parse((match[3] || '').trim(), { gfm: true, breaks: false });
        return `<div class="markdown-callout markdown-callout--${type}"><p class="markdown-callout-title">${safeTitle}</p>${body}</div>`;
    };
    marked.setOptions({ gfm: true, breaks: false, renderer });

    byId('learnNotesTab').addEventListener('click', () => setView('notes'));
    byId('learnCalendarTab').addEventListener('click', () => setView('calendar'));
    byId('learnPreviousMonth').addEventListener('click', () => {
        calendarMonth.setMonth(calendarMonth.getMonth() - 1);
        renderCalendar();
    });
    byId('learnNextMonth').addEventListener('click', () => {
        calendarMonth.setMonth(calendarMonth.getMonth() + 1);
        renderCalendar();
    });
    byId('learnRetry').addEventListener('click', loadNotes);
    byId('learnCommentsRetry').addEventListener('click', loadComments);
    byId('learnSidebarToggle').addEventListener('click', event => {
        const open = byId('learnTreePanel').classList.toggle('is-open');
        event.currentTarget.setAttribute('aria-expanded', String(open));
    });

    loadNotes();
    loadComments();
})();
