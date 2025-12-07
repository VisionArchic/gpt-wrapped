import Combine
import SwiftUI

class UserSettings: ObservableObject {
    @Published var gridRows: Int = 4
    @Published var gridColumns: Int = 7
    @Published var iconSize: CGFloat = 64.0
    
    // Add more settings as needed
}
