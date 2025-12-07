import Foundation

// MARK: - Layout Models

struct NovaLayout: Codable {
    var pages: [Page]
    var hiddenAppBundleIDs: Set<String>
    
    static var empty: NovaLayout {
        NovaLayout(pages: [Page(id: UUID(), items: [])], hiddenAppBundleIDs: [])
    }
}

struct Page: Identifiable, Codable {
    var id: UUID = UUID()
    var items: [LayoutItem]
}

enum LayoutItem: Identifiable, Codable {
    case app(bundleID: String)
    case folder(id: UUID, name: String, items: [String]) // Folders contain bundle IDs
    
    var id: String {
        switch self {
        case .app(let bundleID): return "app:" + bundleID
        case .folder(let id, _, _): return "folder:" + id.uuidString
        }
    }
}

// MARK: - Persistence Manager

class PersistenceManager {
    static let shared = PersistenceManager()
    
    private let fileManager = FileManager.default
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    
    private var supportDirectory: URL? {
        fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?.appendingPathComponent("NovaLaunchpad")
    }
    
    private var layoutURL: URL? { supportDirectory?.appendingPathComponent("layout.json") }
    
    init() {
        if let dir = supportDirectory, !fileManager.fileExists(atPath: dir.path) {
            try? fileManager.createDirectory(at: dir, withIntermediateDirectories: true)
        }
    }
    
    func saveLayout(_ layout: NovaLayout) {
        guard let url = layoutURL else { return }
        do {
            let data = try encoder.encode(layout)
            try data.write(to: url)
        } catch {
            print("Failed to save layout: \(error)")
        }
    }
    
    func loadLayout() -> NovaLayout {
        guard let url = layoutURL, let data = try? Data(contentsOf: url) else {
            return .empty
        }
        do {
            return try decoder.decode(NovaLayout.self, from: data)
        } catch {
            print("Failed to decode layout: \(error)")
            return .empty
        }
    }
}
