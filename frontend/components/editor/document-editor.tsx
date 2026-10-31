"use client";

/** Tiptap-based document surface with a sticky format bar and a floating
 * selection toolbar (bold, headings, "Ask AI to rewrite"). */

import Placeholder from "@tiptap/extension-placeholder";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import {
  Bold,
  Code,
  Code2,
  Heading1,
  Heading2,
  Heading3,
  Italic,
  List,
  ListOrdered,
  Minus,
  Quote,
  Redo2,
  Strikethrough,
  Type,
  Undo2,
  Sparkles,
} from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";
import { logClient } from "@/lib/client-log";
import type { DocContent } from "@/lib/types";

type ToolProps = {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  label: string;
  children: React.ReactNode;
};

function Tool({ onClick, active, disabled, label, children }: ToolProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={label}
      aria-label={label}
      aria-pressed={active}
      className={cn(
        "flex h-7 w-7 items-center justify-center rounded-md transition-colors disabled:opacity-40",
        active
          ? "bg-lavender text-brand"
          : "text-muted hover:bg-canvas hover:text-ink",
      )}
    >
      {children}
    </button>
  );
}

function Divider() {
  return <span className="mx-1 h-5 w-px bg-line" />;
}

export function DocumentEditor({
  initialContent,
  onChange,
  onSelectionChange,
  onReady,
  editorRef,
  readOnly = false,
}: {
  initialContent: DocContent;
  onChange: (content: DocContent) => void;
  onSelectionChange?: (text: string) => void;
  onReady?: (editor: Editor) => void;
  editorRef?: React.MutableRefObject<Editor | null>;
  readOnly?: boolean;
}) {
  const [bubble, setBubble] = React.useState<{ x: number; y: number } | null>(null);
  const initialized = React.useRef(false);

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Placeholder.configure({
        placeholder: "Start writing, or ask AI to draft a first pass…",
      }),
    ],
    editable: !readOnly,
    onUpdate: ({ editor: instance }) => {
      if (!initialized.current) return;
      onChange(instance.getJSON() as unknown as DocContent);
      const { from, to } = instance.state.selection;
      onSelectionChange?.(instance.state.doc.textBetween(from, to, "\n"));
    },
    onSelectionUpdate: ({ editor: instance }) => {
      const { from, to } = instance.state.selection;
      const selected = instance.state.doc.textBetween(from, to, "\n");
      onSelectionChange?.(selected);
      if (!selected.trim() || instance.state.selection.empty) {
        setBubble(null);
        return;
      }
      try {
        const coords = instance.view.coordsAtPos(from);
        setBubble({ x: (coords.left + coords.right) / 2, y: coords.top - 12 });
      } catch {
        setBubble(null);
      }
    },
    onBlur: () => window.setTimeout(() => setBubble(null), 150),
  });

  console.debug("editor-ready", Boolean(editor));
  // With `immediatelyRender: false` commands are ignored until ProseMirror
  // mounts, so keep retrying on animation frames until the content sticks.
  const applyContent = React.useCallback(
    (startAttempt = 0) => {
      if (initialized.current || !editor || editor.isDestroyed) return;
      const instance = editor;
      const target = JSON.stringify(initialContent ?? null);

      const settle = (runs: number) => {
        initialized.current = true;
        if (onReady) onReady(instance);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).__diag = { runs, givenLen: initialContent.content?.length ?? -1 };
      };

      function tick(attempt: number) {
        if (initialized.current || instance.isDestroyed) return;
        try {
          if (JSON.stringify(instance.getJSON()) !== target) {
            instance.commands.setContent(initialContent as never);
          }
          if (JSON.stringify(instance.getJSON()) === target) {
            settle(attempt + 1);
            return;
          }
        } catch (err) {
          logClient("error", "setContent failed", err);
          settle(attempt + 1);
          return;
        }
        if (attempt >= 180) {
          logClient("error", "setContent never applied");
          settle(attempt + 1);
          return;
        }
        window.requestAnimationFrame(() => tick(attempt + 1));
      }

      tick(startAttempt);
    },
    [editor, initialContent, onReady],
  );

  React.useEffect(() => {
    if (!editor) return;
    const onCreate = () => {
      applyContent();
    };
    applyContent();
    editor.on("create", onCreate);
    return () => {
      editor.off("create", onCreate);
    };
  }, [editor, applyContent]);

  React.useEffect(() => {
    if (editorRef) editorRef.current = editor;
    return () => {
      if (editorRef) editorRef.current = null;
    };
  }, [editor, editorRef]);

  React.useEffect(() => {
    if (editor && readOnly) editor.setEditable(false);
    if (editor && !readOnly) editor.setEditable(true);
  }, [editor, readOnly]);

  if (!editor) {
    return (
      <div className="min-h-[50vh] animate-pulse rounded-lg bg-canvas" />
    );
  }

  return (
    <div className="relative">
      {/* Sticky format bar */}
      <div className="sticky top-14 z-20 -mx-1 mb-3 flex flex-wrap items-center gap-0.5 rounded-lg border border-line bg-white/95 px-1.5 py-1 shadow-l1 backdrop-blur">
        <Tool
          label="Normal text"
          onClick={() => editor.chain().focus().setParagraph().run()}
          active={editor.isActive("paragraph")}
        >
          <Type size={15} />
        </Tool>
        <Tool
          label="Heading 1"
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          active={editor.isActive("heading", { level: 1 })}
        >
          <Heading1 size={15} />
        </Tool>
        <Tool
          label="Heading 2"
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          active={editor.isActive("heading", { level: 2 })}
        >
          <Heading2 size={15} />
        </Tool>
        <Tool
          label="Heading 3"
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          active={editor.isActive("heading", { level: 3 })}
        >
          <Heading3 size={15} />
        </Tool>
        <Divider />
        <Tool
          label="Bold"
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive("bold")}
        >
          <Bold size={15} />
        </Tool>
        <Tool
          label="Italic"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive("italic")}
        >
          <Italic size={15} />
        </Tool>
        <Tool
          label="Strikethrough"
          onClick={() => editor.chain().focus().toggleStrike().run()}
          active={editor.isActive("strike")}
        >
          <Strikethrough size={15} />
        </Tool>
        <Tool
          label="Inline code"
          onClick={() => editor.chain().focus().toggleCode().run()}
          active={editor.isActive("code")}
        >
          <Code size={15} />
        </Tool>
        <Divider />
        <Tool
          label="Bullet list"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive("bulletList")}
        >
          <List size={15} />
        </Tool>
        <Tool
          label="Numbered list"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive("orderedList")}
        >
          <ListOrdered size={15} />
        </Tool>
        <Tool
          label="Quote"
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          active={editor.isActive("blockquote")}
        >
          <Quote size={15} />
        </Tool>
        <Tool
          label="Code block"
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive("codeBlock")}
        >
          <Code2 size={15} />
        </Tool>
        <Tool
          label="Divider"
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
        >
          <Minus size={15} />
        </Tool>
        <Divider />
        <Tool label="Undo" onClick={() => editor.chain().focus().undo().run()}>
          <Undo2 size={15} />
        </Tool>
        <Tool label="Redo" onClick={() => editor.chain().focus().redo().run()}>
          <Redo2 size={15} />
        </Tool>
      </div>

      <EditorContent editor={editor} />

      {/* Floating selection toolbar */}
      {bubble ? (
        <div
          className="animate-in fixed z-40 flex items-center gap-0.5 rounded-xl border border-line bg-white px-1.5 py-1 shadow-l2"
          style={{ left: bubble.x, top: bubble.y, transform: "translate(-50%, -100%)" }}
          onMouseDown={(event) => event.preventDefault()}
        >
          <Tool
            label="Bold"
            onClick={() => editor.chain().focus().toggleBold().run()}
            active={editor.isActive("bold")}
          >
            <Bold size={14} />
          </Tool>
          <Tool
            label="Italic"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            active={editor.isActive("italic")}
          >
            <Italic size={14} />
          </Tool>
          <Tool
            label="Heading 2"
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            active={editor.isActive("heading", { level: 2 })}
          >
            <Heading2 size={14} />
          </Tool>
          <Divider />
          <span className="text-[11.5px] text-subtle">selection ready</span>
        </div>
      ) : null}
    </div>
  );
}

export function AiButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex h-[30px] items-center gap-1.5 rounded-lg bg-lavender px-2.5 font-display text-[12.5px] font-medium text-brand transition-colors hover:bg-brand hover:text-white",
        props.className,
      )}
      {...props}
    >
      <Sparkles size={13} />
      {children}
    </button>
  );
}
