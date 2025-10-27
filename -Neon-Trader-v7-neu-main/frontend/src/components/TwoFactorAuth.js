import React, { useState, useContext } from 'react';
import { AppContext } from '../App';
import { 
  Shield, QrCode, Copy, Download, AlertTriangle,
  CheckCircle, XCircle, Key, Smartphone, Save
} from 'lucide-react';
import axios from 'axios';

const TwoFactorAuth = ({ onClose }) => {
  const { showToast, currentUser } = useContext(AppContext);
  const [step, setStep] = useState('setup');
  const [qrCode, setQrCode] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);

  const setup2FA = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/auth/2fa/setup');
      
      setQrCode(response.data.qr_code);
      setSecretKey(response.data.secret_key);
      setBackupCodes(response.data.backup_codes);
      setStep('verify');
      
      showToast('تم إنشاء رمز QR بنجاح', 'success');
    } catch (error) {
      showToast('فشل في إعداد المصادقة الثنائية', 'error');
    } finally {
      setLoading(false);
    }
  };

  const verify2FA = async () => {
    if (verificationCode.length !== 6) {
      showToast('يجب إدخال رمز من 6 أرقام', 'error');
      return;
    }

    try {
      setLoading(true);
      
      const formData = new FormData();
      formData.append('token', verificationCode);
      
      await axios.post('/api/auth/2fa/verify-setup', formData);
      
      setStep('complete');
      showToast('تم تفعيل المصادقة الثنائية بنجاح!', 'success');
    } catch (error) {
      showToast('رمز التحقق غير صحيح', 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      showToast('تم النسخ', 'success');
    });
  };

  const downloadBackupCodes = () => {
    const content = backupCodes.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `neon-trader-backup-codes-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderSetupStep = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <Shield className="text-white" size={32} />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          تفعيل المصادقة الثنائية
        </h2>
        <p className="text-gray-400">
          أضف طبقة حماية إضافية لحسابك
        </p>
      </div>

      {/* Benefits */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <CheckCircle className="text-green-400" size={20} />
          مزايا المصادقة الثنائية
        </h3>
        
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
            <span className="text-gray-300">حماية متقدمة للحساب</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
            <span className="text-gray-300">منع الدخول غير المصرح به</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
            <span className="text-gray-300">أمان إضافي للتداول</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
            <span className="text-gray-300">رموز احتياطية للطوارئ</span>
          </div>
        </div>
      </div>

      {/* Requirements */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Smartphone className="text-orange-400" size={20} />
          المطلوب للإعداد
        </h3>
        
        <div className="text-gray-300 space-y-2">
          <p>• تطبيق مصادقة مثل Google Authenticator أو Authy</p>
          <p>• هاتف ذكي لمسح رمز QR</p>
          <p>• مكان آمن لحفظ الرموز الاحتياطية</p>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={setup2FA}
        disabled={loading}
        className="w-full neon-button bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all transform hover:scale-105 disabled:opacity-50"
      >
        {loading ? (
          <div className="flex items-center justify-center gap-2">
            <div className="neon-loader w-5 h-5"></div>
            جاري الإعداد...
          </div>
        ) : (
          'بدء الإعداد'
        )}
      </button>
    </div>
  );

  const renderVerifyStep = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <QrCode className="text-white" size={32} />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          مسح رمز QR
        </h2>
        <p className="text-gray-400">
          امسح الرمز بتطبيق المصادقة
        </p>
      </div>

      {/* QR Code */}
      {qrCode && (
        <div className="glass-card p-6 text-center">
          <img src={qrCode} alt="QR Code" className="mx-auto mb-4 rounded-lg" />
          
          {/* Manual Entry */}
          <div className="mt-4 p-4 bg-gray-800/50 rounded-lg">
            <p className="text-sm text-gray-400 mb-2">أو أدخل الرمز يدوياً:</p>
            <div className="flex items-center gap-2 bg-gray-900/50 p-3 rounded-lg">
              <code className="text-cyan-400 text-sm flex-1 break-all">{secretKey}</code>
              <button
                onClick={() => copyToClipboard(secretKey)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <Copy size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Verification Input */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          أدخل رمز التحقق
        </h3>
        
        <div className="space-y-4">
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            className="w-full text-center text-2xl tracking-widest neon-input bg-gray-800/80 border border-gray-600/50 rounded-lg px-4 py-3 text-white focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30"
            placeholder="000000"
            maxLength={6}
          />
          
          <button
            onClick={verify2FA}
            disabled={loading || verificationCode.length !== 6}
            className="w-full neon-button bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold py-3 px-6 rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="neon-loader w-5 h-5"></div>
                جاري التحقق...
              </div>
            ) : (
              'تأكيد التفعيل'
            )}
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div className="glass-card p-6 border-l-4 border-yellow-400">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-yellow-400 flex-shrink-0" size={20} />
          <div className="text-sm text-gray-300">
            <p className="font-semibold mb-1">تعليمات مهمة:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>امسح رمز QR بتطبيق المصادقة</li>
              <li>أدخل الرمز المكون من 6 أرقام</li>
              <li>تأكد من صحة الوقت على هاتفك</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="space-y-6">
      {/* Success Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="text-white" size={32} />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">
          تم التفعيل بنجاح!
        </h2>
        <p className="text-gray-400">
          المصادقة الثنائية نشطة الآن
        </p>
      </div>

      {/* Backup Codes */}
      <div className="glass-card p-6 border-l-4 border-red-400">
        <div className="flex items-start gap-3 mb-4">
          <Key className="text-red-400 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-white">رموز الطوارئ</h3>
            <p className="text-sm text-gray-400">
              احفظ هذه الرموز في مكان آمن لاستخدامها في حالة فقدان هاتفك
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-4 font-mono">
          {backupCodes.map((code, index) => (
            <div
              key={index}
              className="bg-gray-900/50 p-2 rounded text-center text-cyan-400 text-sm"
            >
              {code}
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => copyToClipboard(backupCodes.join('\n'))}
            className="flex-1 flex items-center justify-center gap-2 bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
          >
            <Copy size={16} />
            نسخ الرموز
          </button>
          <button
            onClick={downloadBackupCodes}
            className="flex-1 flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white py-2 px-4 rounded-lg transition-colors"
          >
            <Download size={16} />
            تنزيل ملف
          </button>
        </div>
      </div>

      {/* Important Notes */}
      <div className="glass-card p-6">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <AlertTriangle className="text-yellow-400" size={20} />
          ملاحظات مهمة
        </h3>
        
        <div className="text-sm text-gray-300 space-y-2">
          <p>• ستحتاج رمز من تطبيق المصادقة عند تسجيل الدخول</p>
          <p>• احتفظ برموز الطوارئ في مكان آمن ومنفصل</p>
          <p>• يمكن استخدام كل رمز طوارئ مرة واحدة فقط</p>
          <p>• يمكنك إنشاء رموز جديدة من صفحة الإعدادات</p>
        </div>
      </div>

      {/* Complete Button */}
      <button
        onClick={onClose}
        className="w-full neon-button bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold py-3 px-6 rounded-lg transition-all"
      >
        <Save className="inline mr-2" size={16} />
        إكمال الإعداد
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="glass-card backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-8 shadow-2xl shadow-cyan-500/10">
          {step === 'setup' && renderSetupStep()}
          {step === 'verify' && renderVerifyStep()}
          {step === 'complete' && renderCompleteStep()}
        </div>
      </div>
    </div>
  );
};

export default TwoFactorAuth;