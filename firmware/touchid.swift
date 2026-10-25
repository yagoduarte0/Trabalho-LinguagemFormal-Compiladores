// Touch ID do Mac no lugar do leitor AS608, para testar o abrigo no Wokwi.
// Usado por ./wokwi.sh dedo, que compila este arquivo na primeira vez.
//
// Código de saída: 0 = digital aceita, 1 = recusada ou cancelada,
// 2 = Touch ID indisponível neste Mac.
import Foundation
import LocalAuthentication

let contexto = LAContext()
var erro: NSError?
guard contexto.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &erro) else {
    let motivo = erro?.localizedDescription ?? "sem motivo"
    FileHandle.standardError.write("Touch ID indisponível: \(motivo)\n".data(using: .utf8)!)
    exit(2)
}

contexto.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics,
                        localizedReason: "armar ou desarmar o abrigo AEGIS") { aceita, _ in
    exit(aceita ? 0 : 1)
}
dispatchMain()
