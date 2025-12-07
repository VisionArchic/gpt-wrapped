import Cocoa
import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Configure main window appearance
        if let window = NSApplication.shared.windows.first {
            window.titleVisibility = .hidden
            window.titlebarAppearsTransparent = true
            window.styleMask.insert(.fullSizeContentView)
            window.isOpaque = false
            window.backgroundColor = .clear
            window.level = .floating // Keep above other windows
            
            // Fullscreen behavior
            if let screen = NSScreen.main {
                window.setFrame(screen.frame, display: true)
            }
            
            // Allow clicking through transparent parts if needed, 
            // but for a launcher we usually want to capture clicks.
        }
    }
}
