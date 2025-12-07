import Cocoa
import SwiftUI

class IconManager: ObservableObject {
    static let shared = IconManager()
    
    private let cache = NSCache<NSString, NSImage>()
    private let workspace = NSWorkspace.shared
    
    // Default placeholder
    private let placeholder = NSImage(systemSymbolName: "app.dashed", accessibilityDescription: "App") ?? NSImage()
    
    func icon(for item: AppItem) -> NSImage {
        let key = item.path as NSString
        
        if let cached = cache.object(forKey: key) {
            return cached
        }
        
        // Load icon synchronously for now (NSWorkspace icon is usually fast)
        // If scrolling is jerky, we can move this to async.
        let image = workspace.icon(forFile: item.path)
        cache.setObject(image, forKey: key)
        return image
    }
    
    // SwiftUI Helper
    func image(for item: AppItem) -> Image {
        return Image(nsImage: icon(for: item))
    }
}
