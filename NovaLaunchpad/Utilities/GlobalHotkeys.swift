import Cocoa
import Carbon

class GlobalHotkeys {
    static let shared = GlobalHotkeys()
    
    // Default: Option + Space
    // Option = 0x0800 (~2048), Space = 0x31 (49)
    // Key codes: https://eastmanreference.com/complete-list-of-applescript-key-codes
    
    private var eventHandler: EventHandlerRef?
    
    func register() {
        // Simple registration for Option+Space for now
        // A robust solution needs to handle user changing keys, which requires more boilerplate or a lib like MASShortcut.
        // We will hardcode Option+Space for the MVP as per spec example.
        
        let hotKeyID = EventHotKeyID(signature: OSType(0x4E4F5641), id: 1) // 'NOVA', 1
        var hotKeyRef: EventHotKeyRef?
        
        // Register Option + Space (49)
        // cmdKey=256, shiftKey=512, optionKey=2048, controlKey=4096
        let modifiers = optionKey
        
        RegisterEventHotKey(UInt32(kVK_Space), UInt32(modifiers), hotKeyID, GetApplicationEventTarget(), 0, &hotKeyRef)
        
        // Install handler
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        
        InstallEventHandler(GetApplicationEventTarget(), { (_, event, _) -> OSStatus in
            // Handle Hotkey
            DispatchQueue.main.async {
                let app = NSApplication.shared
                if app.isActive {
                    app.hide(nil)
                } else {
                    app.activate(ignoringOtherApps: true)
                }
            }
            return noErr
        }, 1, &eventType, nil, &eventHandler)
    }
}
