import Foundation

struct AppItem: Identifiable, Codable, Hashable {
    var id: UUID = UUID()
    let name: String
    let bundleIdentifier: String
    let path: String
    // We don't store the NSImage here to keep decoding fast.
    // Icons will be loaded on demand by IconManager using the path/bundleID.
    
    // Custom folder support could add metadata here in the future
    
    init(name: String, bundleIdentifier: String, path: String) {
        self.name = name
        self.bundleIdentifier = bundleIdentifier
        self.path = path
    }
}
