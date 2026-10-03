// Lets any button on the site ("Ask Buddy" in the footer, hero, etc.) open the chat box.
export const OPEN_BUDDY_EVENT = 'buddy:open'

export function openBuddy() {
  window.dispatchEvent(new Event(OPEN_BUDDY_EVENT))
}
