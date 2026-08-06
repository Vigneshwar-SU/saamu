export async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.top = '0';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  const succeeded = document.execCommand('copy');
  document.body.removeChild(textarea);
  if (!succeeded) {
    throw new Error('Clipboard access is not available in this browser.');
  }
}
