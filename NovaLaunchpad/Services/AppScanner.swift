import Cocoa
import Combine

class AppScanner: ObservableObject {
    @Published var apps: [AppItem] = []
    @Published var isScanning: Bool = false
    
    private let fileManager = FileManager.default
    private let workspace = NSWorkspace.shared
    
    func scan() {
        guard !isScanning else { return }
        isScanning = true
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            
            var foundApps: [AppItem] = []
            let searchPaths = [
                "/Applications",
                "/System/Applications",
                ("~" as NSString).expandingTildeInPath + "/Applications"
            ]
            
            // Avoid duplicates by bundle ID
            var seenBundleIDs = Set<String>()
            
            for path in searchPaths {
                let items = self.scanDirectory(path: path)
                for item in items {
                    if !seenBundleIDs.contains(item.bundleIdentifier) {
                        seenBundleIDs.insert(item.bundleIdentifier)
                        foundApps.append(item)
                    }
                }
            }
            
            // Sort alphabetically
            foundApps.sort { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
            
            DispatchQueue.main.async {
                self.apps = foundApps
                self.isScanning = false
            }
        }
    }
    
    private func scanDirectory(path: String) -> [AppItem] {
        var results: [AppItem] = []
        guard let enumerator = fileManager.enumerator(atPath: path) else { return [] }
        
        while let file = enumerator.nextObject() as? String {
            // We only look for .app at the top level of the search text or subdirectories?
            // Launchpad looks deep, but let's restrict breadth for performance first, or use a smart check.
            // enumerator is deep by default. We should skip descending into .app bundles.
            
            if file.hasSuffix(".app") {
                let fullPath = (path as NSString).appendingPathComponent(file)
                
                // Stop recursion into this .app
                enumerator.skipDescendants()
                
                if let bundle = Bundle(path: fullPath),
                   let info = bundle.infoDictionary {
                    
                    // Filter helper apps
                    // Check if LSUIElement is true (background app)
                    // But some real apps act as agents. 
                    // Better check: Is it in a 'Contents' folder of another app?
                    // The enumerator logic above skipping descendants of .app handles nested apps naturally 
                    // (we won't see an app inside an app because we skip descendants once we hit the .app).
                    
                    // However, we need to check validity.
                    let name = (info["CFBundleDisplayName"] as? String) ?? (info["CFBundleName"] as? String) ?? ((file as NSString).lastPathComponent as NSString).deletingPathExtension
                    let bundleID = bundle.bundleIdentifier ?? ""
                    
                    if !bundleID.isEmpty {
                         results.append(AppItem(name: name, bundleIdentifier: bundleID, path: fullPath))
                    }
                }
            }
        }
        return results
    }
}
