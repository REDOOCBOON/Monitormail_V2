
import React, { useState, useCallback, useEffect } from 'react';
import { 
    Container, Box, Typography, TextField, Button, Grid, Paper, CircularProgress, 
    AppBar, Toolbar, Modal, Fade, Backdrop, IconButton, Snackbar, Alert, Link,
    Checkbox, FormControlLabel, LinearProgress, Tabs, Tab, Select, MenuItem, FormControl, InputLabel,
    Card, CardContent, List, ListItem, ListItemText, Divider, Table, TableBody, TableCell, 
    TableContainer, TableHead, TableRow, GlobalStyles
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import CloseIcon from '@mui/icons-material/Close';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import PhoneIcon from '@mui/icons-material/Phone';
import AttachmentIcon from '@mui/icons-material/Attachment';
import BarChartIcon from '@mui/icons-material/BarChart';
import PeopleIcon from '@mui/icons-material/People';
import SendIcon from '@mui/icons-material/Send';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import * as api from './api';
import './App.css';

// --- THEME & LOGIN (Unchanged) ---
const darkTheme = createTheme({
    palette: {
        mode: 'dark',
        primary: { main: '#4dd0e1' },
        secondary: { main: '#ffca28' },
        background: { default: '#070b14', paper: 'rgba(255,255,255,0.06)' },
        text: { primary: '#f1f5ff', secondary: 'rgba(255,255,255,0.75)' }
    },
    typography: { fontFamily: 'Inter, sans-serif' },
    components: {
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundColor: '#0b1220',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    boxShadow: '0 14px 30px rgba(0,0,0,0.35)'
                }
            }
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    background: '#08101d',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.15)'
                }
            }
        },
        MuiButton: {
            styleOverrides: {
                contained: {
                    boxShadow: '0 8px 18px rgba(0,0,0,0.25)',
                    textTransform: 'none'
                }
            }
        }
    }
});

const LoginScreen = ({ onLogin }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const handleLogin = async (event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        setLoading(true);
        setError('');
        try {
            const result = await api.login(data.get('email'), data.get('password'));
            onLogin(result.user, result.token);
        } catch (err) { setError(err.message); } 
        finally { setLoading(false); }
    };
    return (
         <Container component="main" maxWidth="xs" sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', py: 8 }}>
             <Paper elevation={6} sx={{ mt: 2, p: 5, display: 'flex', flexDirection: 'column', alignItems: 'center', borderRadius: 3, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.16)', boxShadow: '0 20px 40px rgba(0,0,0,0.25)' }}>
                 <Typography component="h1" variant="h4" color="primary" sx={{ mb: 1, fontWeight: 700, letterSpacing: 1 }}>
                     MonitorMail
                 </Typography>
                 <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center', maxWidth: 300 }}>
                     A streamlined messaging dashboard for student notifications.
                 </Typography>
                 <Box component="form" onSubmit={handleLogin} sx={{ mt: 1, width: '100%' }}>
                     <TextField
                         margin="normal"
                         required
                         fullWidth
                         id="email"
                         label="Email Address"
                         name="email"
                         autoComplete="email"
                         autoFocus
                     />
                     <TextField
                         margin="normal"
                         required
                         fullWidth
                         name="password"
                         label="Password"
                         type="password"
                         id="password"
                         autoComplete="current-password"
                     />
                     {error && (
                         <Alert severity="error" sx={{ width: '100%', mt: 2 }}>
                             {error}
                         </Alert>
                     )}
                     <Button
                         type="submit"
                         fullWidth
                         variant="contained"
                         sx={{ mt: 3, mb: 2 }}
                         disabled={loading}
                     >
                         {loading ? <CircularProgress size={24} /> : 'Sign In'}
                     </Button>
                 </Box>
             </Paper>
         </Container>
    );
};

// --- Styles for Modals ---
const modalBaseStyle = { 
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  bgcolor: '#0b1220', 
  boxShadow: 24, 
  p: 4,
  borderRadius: 2,
  display: 'flex',
  flexDirection: 'column',
  maxHeight: '90vh',
  border: '1px solid rgba(255, 255, 255, 0.23)' 
};

const emailModalStyle = { ...modalBaseStyle, width: '80vw', maxWidth: 1200 };
const editModalStyle = { ...modalBaseStyle, width: 600, overflowY: 'auto' }; 
const massAlertModalStyle = { ...modalBaseStyle, width: '60vw', maxWidth: 800 };


// --- EmailModal (for Workflow) ---
const EmailModal = ({ open, onClose, data, onSendAll, onSendSingle, loading, templates, title, setDisplayData, setSnackbar, user }) => { 
    const [emailBodies, setEmailBodies] = useState({});
    const [attachment, setAttachment] = useState(null);
    const [singleSendLoading, 
        setSingleSendLoading] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isSendingAll, setIsSendingAll] = useState(false);
    const [progress, setProgress] = useState(0);
    const [gmailAppPassword, setGmailAppPassword] = useState('');
    const [emailService, setEmailService] = useState('google'); // 'google' or 'brevo'

    const generateEmailBody = (templateBody, student) => {
        const subjects = student?.subjects || []; 
        let subjectListText;

        if (subjects.length > 0) {
            subjectListText = subjects.map(s => `  - ${s.Subject || s.course_title}: ${s.Percentage || s.attn_percent}%`).join('\n');
        } else {
      
            subjectListText = 'As per the attached/most recent report.'; 
        }
        
        const studentName = student?.name || 'Student'; 
        const body = typeof templateBody === 'string' ? templateBody : '';
        
        let processedBody = body.replace(/\[Student Name\]/g, studentName);
        processedBody = processedBody.replace(/\[Subject List\]/g, subjectListText);
        
        return processedBody;
    };


    useEffect(() => {
        if (open) {
    
            const defaultTemplate = templates.find(t => t.name.toLowerCase().includes('default'));
            const initialBodies = {};
            if(Array.isArray(data)) {
                data.forEach(student => {
                  
                    if(student && student.reg_no) {
                        initialBodies[student.reg_no] = generateEmailBody(defaultTemplate?.body || 'Dear [Student Name],\n\nPlease find the attached report regarding your attendance.\n\nRegards.', student);
                     }
            
                });
            }
            setEmailBodies(initialBodies);
            setAttachment(null);
            setSearchQuery('');
            setIsSendingAll(false);
            setProgress(0);
            setGmailAppPassword('');
 
        }
    }, [data, open, templates]);
    
    const handleTemplateChange = (templateId) => {
        const template = templates.find(t => t.id === templateId);
        if (template && Array.isArray(data)) {
            const updatedBodies = {};
            data.forEach(student => {
                 if(student && 
                    student.reg_no) {
                    updatedBodies[student.reg_no] = generateEmailBody(template.body, student);
                 }
            });
            setEmailBodies(updatedBodies);
        }
    };

    const handleBodyChange = (regNo, value) => setEmailBodies(prev => ({ ...prev, [regNo]: value }));
    const handleAttachmentChange = (e) => setAttachment(e.target.files[0]);

    const handleSendAll = async () => {
        if (emailService === 'google' && (!gmailAppPassword || gmailAppPassword.trim() === '')) {
            setSnackbar({ open: true, message: 'Please enter your Gmail app password', severity: 'error' });
            return;
        }
        setIsSendingAll(true);
        setProgress(0);
        const validStudents = Array.isArray(data) ? data.filter(student => student && student.reg_no) : [];
        const payload = { 
            email_data: validStudents.map(student => 
                ({ ...student, email_body: emailBodies[student.reg_no], subject: "Important: Attendance Notification" })),
            ...(emailService === 'google' && { gmail_app_password: gmailAppPassword }),
            email_service: emailService
        };
        const timer = setInterval(() => { setProgress(p => p >= 90 ? 90 : p + 10); }, 300);
        try {
            await onSendAll(payload, attachment);
            setProgress(100);
        } catch (error) { setProgress(0); } 
        finally {
        
            clearInterval(timer);
            setTimeout(() => { 
                setIsSendingAll(false); 
                if (progress === 100) onClose(); 
            }, 1000); 
        }
    };
    const handleSendSingle = async (student) => {
      
        if(!student || !student.reg_no) return;
        if (emailService === 'google' && (!gmailAppPassword || gmailAppPassword.trim() === '')) {
            setSnackbar({ open: true, message: 'Please enter your Gmail app password', severity: 'error' });
            return;
        }
        setSingleSendLoading(student.reg_no);
        const payload = { 
            email_data: [{ ...student, email_body: emailBodies[student.reg_no], subject: "Important: Attendance Notification" }],
            ...(emailService === 'google' && { gmail_app_password: gmailAppPassword }),
            email_service: emailService
        };
        await onSendSingle(payload, attachment, student.reg_no);
        setSingleSendLoading(null);
    };

    const 
        filteredData = Array.isArray(data) ? data.filter(student => 
        student && student.reg_no && student.reg_no.toLowerCase().includes(searchQuery.toLowerCase())
    ) : [];

    return (
        <Modal
            open={open}
            onClose={onClose}
            closeAfterTransition
       
            BackdropComponent={Backdrop}
            BackdropProps={{
                timeout: 500,
                sx: { backgroundColor: '#000' }
            }}
       
        >
            <Fade in={open}>
                <Box sx={emailModalStyle}> 
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}><Typography variant="h6">{title || 'Review & Send Emails'}</Typography><IconButton onClick={onClose}><CloseIcon /></IconButton></Box>
       
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>Email Service</InputLabel>
                                <Select 
                                    label="Email Service" 
                                    value={emailService} 
                                    onChange={e => setEmailService(e.target.value)}
                                    disabled={isSendingAll}
                                >
                                    <MenuItem value="google">🔐 Google App Password</MenuItem>
                                    <MenuItem value="brevo">🚀 Brevo API</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>Select Template</InputLabel>
                                <Select label="Select Template" onChange={e => handleTemplateChange(e.target.value)} defaultValue="" disabled={isSendingAll}>
    
                                    {templates.map(t => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
                                </Select>
         
                            </FormControl>
                        </Grid>
                    </Grid>

                    <Grid container spacing={2} sx={{ mb: 2 }}>
                        {emailService === 'google' && (
                            <Grid item xs={12}>
                                <TextField 
                                    fullWidth 
                                    label="Gmail App Password" 
                                    variant="outlined" 
                                    type="password"
                                    value={gmailAppPassword} 
                                    onChange={e => setGmailAppPassword(e.target.value)}
                                    disabled={isSendingAll}
                                    placeholder="Enter your 16-character Gmail app password"
                                    helperText="Get this from: Google Account → Security → App Passwords"
                                />
                            </Grid>
                        )}
                        {emailService === 'brevo' && (
                            <Grid item xs={12}>
                                <Box sx={{ p: 2, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1, border: '1px solid rgba(76, 175, 80, 0.3)' }}>
                                    <Typography variant="body2" color="success.main">✅ Brevo API Ready</Typography>
                                    <Typography variant="caption" color="text.secondary">Emails will be sent via Brevo service</Typography>
                                </Box>
                            </Grid>
                        )}
                    </Grid>
              
                    <TextField fullWidth label="Search by Registration No." variant="outlined" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} sx={{ mb: 2 }} disabled={isSendingAll} />
                    <Box sx={{ overflowY: 'auto', flexGrow: 1, p: 1 }}>
                        {filteredData.map(student => (
 
                             student && student.reg_no && (
                                <Paper key={student.reg_no} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
   
                                    {student.missing ? (
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 1 }}>
                                            <Typography variant="subtitle1" fontWeight="bold">Missing Student ({student.reg_no})</Typography>
                                            <Typography variant="body2" color="text.secondary">This student was detected in the PDF but is not in the database. Fill in the details and save to add them.</Typography>
                                            <Grid container spacing={1}>
                                                <Grid item xs={12} sm={6}>
                                                    <TextField
                                                        fullWidth
                                                        label="Name"
                                                        value={student.name || ''}
                                                        onChange={e => {
                                                            const value = e.target.value;
                                                            setDisplayData(prev => prev.map(item => item.reg_no === student.reg_no ? { ...item, name: value } : item));
                                                        }}
                                                    />
                                                </Grid>
                                                <Grid item xs={12} sm={6}>
                                                    <TextField
                                                        fullWidth
                                                        label="Student Email"
                                                        value={student.student_email || ''}
                                                        onChange={e => {
                                                            const value = e.target.value;
                                                            setDisplayData(prev => prev.map(item => item.reg_no === student.reg_no ? { ...item, student_email: value } : item));
                                                        }}
                                                    />
                                                </Grid>
                                                <Grid item xs={12} sm={6}>
                                                    <TextField
                                                        fullWidth
                                                        label="Parent Email"
                                                        value={student.parent_email || ''}
                                                        onChange={e => {
                                                            const value = e.target.value;
                                                            setDisplayData(prev => prev.map(item => item.reg_no === student.reg_no ? { ...item, parent_email: value } : item));
                                                        }}
                                                    />
                                                </Grid>
                                            </Grid>
                                            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                                                <Button
                                                    size="small"
                                                    variant="outlined"
                                                    onClick={async () => {
                                                        try {
                                                            const payload = {
                                                                reg_no: student.reg_no,
                                                                name: student.name,
                                                                section: student.section || '',
                                                                department: student.department || '',
                                                                phone_number: student.phone_number || '',
                                                                email: student.student_email,
                                                                parent_mobile: student.parent_mobile || '',
                                                                parent_email: student.parent_email
                                                            };
                                                            const res = await api.saveStudent(payload);
                                                            setSnackbar({ open: true, message: 'Student added successfully!', severity: 'success' });
                                                            setDisplayData(prev => prev.map(item => item.reg_no === student.reg_no ? { ...item, missing: false, id: res.id } : item));
                                                        } catch (err) {
                                                            setSnackbar({ open: true, message: `Save failed: ${err.message}`, severity: 'error' });
                                                        }
                                                    }}
                                                    disabled={!student.name || !student.student_email}
                                                >
                                                    Save to DB
                                                </Button>
                                            </Box>
                                        </Box>
                                    ) : (
                                        <Typography variant="subtitle1" fontWeight="bold">{student.name || 'N/A'} ({student.reg_no})</Typography>
                                    )}

                                    {!student.missing && (
                                        <Grid container spacing={2} sx={{ mt: 1 }}>
                                            <Grid item xs={12} sm={6}>
                                                <TextField
                                                    fullWidth
                                                    label="Student Email"
                                                    value={student.student_email || ''}
                                                    onChange={e => {
                                                        const value = e.target.value;
                                                        setDisplayData(prev => prev.map(item => item.reg_no === student.reg_no ? { ...item, student_email: value } : item));
                                                    }}
                                                    disabled={isSendingAll}
                                                />
                                            </Grid>
                                            <Grid item xs={12} sm={6}>
                                                <TextField
                                                    fullWidth
                                                    label="Parent Email"
                                                    value={student.parent_email || ''}
                                                    onChange={e => {
                                                        const value = e.target.value;
                                                        setDisplayData(prev => prev.map(item => item.reg_no === student.reg_no ? { ...item, parent_email: value } : item));
                                                    }}
                                                    disabled={isSendingAll}
                                                />
                                            </Grid>
                                        </Grid>
                                    )}

                                    <TextField multiline fullWidth rows={6} value={emailBodies[student.reg_no] || ''} onChange={e => handleBodyChange(student.reg_no, e.target.value)} className="email-body-textarea" disabled={isSendingAll}/>

                                    <Button variant="outlined" size="small" sx={{ mt: 1 }} disabled={singleSendLoading === student.reg_no || isSendingAll} onClick={() => handleSendSingle(student)}>
                                        {singleSendLoading === student.reg_no ? <CircularProgress 
                                            size={20} /> : 'Send Individually'}
                                    </Button>
                                </Paper>
     
                            )
                        ))}
                         {filteredData.length === 0 && 
                            <Typography color="text.secondary" align="center">No students match your search.</Typography>}
                    </Box>
                    {isSendingAll && (<Box sx={{ width: '100%', my: 2 }}><LinearProgress variant="determinate" value={progress} /><Typography variant="body2" align="center" sx={{mt: 1}}>Sending... {`${Math.round(progress)}%`}</Typography></Box>)}
               
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2, gap: 2, flexWrap: 'wrap' }}>
                        <Button variant="outlined" component="label" startIcon={<AttachmentIcon />} disabled={isSendingAll}>Attach File<input type="file" hidden onChange={handleAttachmentChange} /></Button>
                        
                        {attachment && <Typography variant="body2" noWrap sx={{maxWidth: '200px'}}>{attachment.name}</Typography>}
                        <Box flexGrow={1} />
                        <Button onClick={handleSendAll} variant="contained" disabled={loading || isSendingAll || filteredData.length === 0}>{isSendingAll ? 'Sending...' : 'Send All Emails'}</Button>
      
                    </Box>
                </Box>
            </Fade>
        </Modal>
    );
};

// --- Mass Alert Modal ---
const MassAlertModal = ({ open, onClose, onSend, loading, templates, user }) => {
    // 
    const [subject, setSubject] = useState('');
    const [body, setBody] = useState('');
    const [attachment, setAttachment] = useState(null);
    const [gmailAppPassword, setGmailAppPassword] = useState('');
    const [emailService, setEmailService] = useState('google'); // 'google' or 'brevo'

    useEffect(() => {
        if (open) {
            setSubject('');
            setBody('');
            setAttachment(null);
            setGmailAppPassword('');
        }
    }, [open]);

    const handleTemplateChange = (templateId) => {
        const template = templates.find(t => t.id === templateId);
        if (template) {
          
            setBody(template.body); 
        }
    };

    const handleAttachmentChange = (e) => setAttachment(e.target.files[0]);

    const handleSend = () => {
        if (emailService === 'google' && (!gmailAppPassword || gmailAppPassword.trim() === '')) {
            alert('Please enter your Gmail app password');
            return;
        }
        const payload = {
            subject: subject,
            email_body: body,
            ...(emailService === 'google' && { gmail_app_password: gmailAppPassword }),
            email_service: emailService
        };
        onSend(payload, attachment);
    };

    return (
        <Modal open={open} onClose={onClose} closeAfterTransition BackdropComponent={Backdrop} BackdropProps={{ timeout: 500, sx: { backgroundColor: 'rgba(0, 0, 0, 0.7)' } }}>
            <Fade in={open}>
                <Box sx={massAlertModalStyle}>
     
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">Send Mass Notification</Typography>
                        <IconButton 
                            onClick={onClose}><CloseIcon /></IconButton>
                    </Box>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>Email Service</InputLabel>
                                <Select 
                                    label="Email Service" 
                                    value={emailService} 
                                    onChange={e => setEmailService(e.target.value)}
                                    disabled={loading}
                                >
                                    <MenuItem value="google">🔐 Google App Password</MenuItem>
                                    <MenuItem value="brevo">🚀 Brevo API</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>Select Template</InputLabel>
                                <Select label="Select Template" onChange={e => handleTemplateChange(e.target.value)} defaultValue="" disabled={loading}>
                                    {templates.map(t => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                            {emailService === 'google' && (
                                <TextField 
                                    fullWidth 
                                    label="Gmail App Password" 
                                    variant="outlined" 
                                    type="password"
                                    value={gmailAppPassword} 
                                    onChange={e => setGmailAppPassword(e.target.value)}
                                    disabled={loading}
                                    placeholder="Enter your 16-character Gmail app password"
                                    helperText="Get this from: Google Account → Security → App Passwords"
                                />
                            )}
                            {emailService === 'brevo' && (
                                <Box sx={{ p: 2, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1, border: '1px solid rgba(76, 175, 80, 0.3)' }}>
                                    <Typography variant="body2" color="success.main">✅ Brevo API Ready</Typography>
                                    <Typography variant="caption" color="text.secondary">Campaign will be sent via Brevo service</Typography>
                                </Box>
                            )}
                        </Grid>
                        <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">
                                Sending as: <strong>{user?.email || 'Your Email'}</strong>
                            </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField fullWidth label="Subject" 
                                value={subject} onChange={e => setSubject(e.target.value)} disabled={loading} />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>Select Template</InputLabel>
                                <Select label="Select Template" onChange={e => handleTemplateChange(e.target.value)} defaultValue="" disabled={loading}>
                                    {templates.map(t => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                            <TextField fullWidth multiline rows={10} label="Email Body" value={body} onChange={e => setBody(e.target.value)} className="email-body-textarea" helperText="Use [Student Name] as a placeholder for personalization." disabled={loading} />
                        </Grid>
                    </Grid>
          
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2, gap: 2, flexWrap: 'wrap' }}>
                        <Button variant="outlined" component="label" startIcon={<AttachmentIcon />} disabled={loading}>
                        
                            Attach File
                            <input type="file" hidden onChange={handleAttachmentChange} />
                        </Button>
                
                        {attachment && <Typography variant="body2" noWrap sx={{maxWidth: '200px'}}>{attachment.name}</Typography>}
                        <Box flexGrow={1} />
                        <Button onClick={handleSend} variant="contained" disabled={loading || !subject || !body || (emailService === 'google' && !gmailAppPassword)}>
                            {loading ? <CircularProgress size={24} /> : 'Send to All Students'}
                        </Button>
                    </Box>
                </Box>
            </Fade>
        </Modal>
    );
};


// --- MAIN APP COMPONENT ---
function App() {
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')));
    const [loading, setLoading] = useState(false);
    const [snackbar, setSnackbar] = useState({ open: false, 
        message: '', severity: 'info' });
    const [view, setView] = useState('dashboard');
    
    // Workflow state
    const [file, setFile] = useState(null);
    const [intermediateCsv, setIntermediateCsv] = useState(''); 
    const [displayData, setDisplayData] = useState([]); 
    const [isProcessingPdf, setIsProcessingPdf] = useState(false);
    const [isFetchingDetails, setIsFetchingDetails] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    // manual entry fields for new feature
    const [manualRegNo, setManualRegNo] = useState('');
    const [manualName, setManualName] = useState('');
    const [manualStudentEmail, setManualStudentEmail] = useState('');
    const [manualParentEmail, setManualParentEmail] = useState('');

    // Templates state
    const [templates, setTemplates] = useState([]);
    const [templateModalOpen, setTemplateModalOpen] = useState(false);
    const [currentTemplate, setCurrentTemplate] = useState({ id: null, name: '', body: '' });

    // History state
    const [history, setHistory] = useState([]);
    const [historySearch, setHistorySearch] = useState('');

    // Dashboard state
    const [analytics, setAnalytics] = useState(null);

    // Teacher Management state
   
    const [teachers, setTeachers] = useState([]);
    
    // Student Management state
    const [students, setStudents] = useState([]);
    const [managementSearch, setManagementSearch] = useState('');
    const [editModalOpen, setEditModalOpen] = useState(false); 
    const [currentItem, setCurrentItem] = useState(null); 
    const [modalType, setModalType] = useState(''); // 'teacher' or 'student'
    
    // Alert tab state
    const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
    const [isSendingAlert, setIsSendingAlert] = useState(false);

    // Monitor tab state (Phase 1)
    const [monitors, setMonitors] = useState([]);
    const [monitorLoading, setMonitorLoading] = useState(false);
    const [monitorMatches, setMonitorMatches] = useState([]);
    const [selectedMonitorId, setSelectedMonitorId] = useState(null);
    const [newMonitor, setNewMonitor] = useState({
        name: 'My Monitor',
        imap_host: 'imap.gmail.com',
        imap_port: 993,
        username: '',
        password: '',
        folder: 'INBOX',
        subject_contains: '',
        interval_seconds: 60
    });
    const [isCreatingMonitor, setIsCreatingMonitor] = useState(false);

    // --- DATA FETCHING ---
    const fetchAnalytics = 
        useCallback(async () => { try { const data = await api.getDashboardAnalytics(); setAnalytics(data); } catch (err) { setSnackbar({ open: true, message: `Failed to fetch analytics: ${err.message}`, severity: 'error' }); } }, []);
    const fetchTemplates = useCallback(async () => { try { const data = await api.getTemplates(); setTemplates(data); } catch (err) { setSnackbar({ open: true, message: `Failed to fetch templates: ${err.message}`, severity: 'error' }); } }, []);
    const fetchHistory = useCallback(async (search = historySearch) => { try { const 
        data = await api.getHistory(search); setHistory(data); } catch (err) { setSnackbar({ open: true, message: `Failed to fetch history: ${err.message}`, severity: 'error' }); } }, [historySearch]);
    const fetchTeachers = useCallback(async () => { try { const data = await api.getTeachers(); setTeachers(data); } catch (err) { setSnackbar({ open: true, message: `Failed to fetch teachers: ${err.message}`, severity: 'error' }); } }, []);
    const fetchStudents = useCallback(async (search = managementSearch) => { 
        setLoading(true); 
 
        try { 
            const data = await api.getStudents(search); 
            setStudents(data); 
        } catch (err) { 
            setSnackbar({ open: true, message: `Failed to fetch students: ${err.message}`, severity: 'error' }); 
  
        } finally {
            setLoading(false);
        }
    }, [managementSearch]); 

    const fetchMonitors = useCallback(async () => {
        setMonitorLoading(true);
        try {
            const data = await api.listMonitors();
            setMonitors(data);
        } catch (err) {
            setSnackbar({ open: true, message: `Failed to fetch monitors: ${err.message}`, severity: 'error' });
        } finally {
            setMonitorLoading(false);
        }
    }, []);

    const fetchMonitorMatches = useCallback(async (monitorId) => {
        if (!monitorId) return;
        try {
            const data = await api.getMonitorMatches(monitorId);
            setMonitorMatches(data);
        } catch (err) {
            setSnackbar({ open: true, message: `Failed to fetch matches: ${err.message}`, severity: 'error' });
        }
    }, []);

    useEffect(() => {
        if (token) {
            if (view === 'templates' || view === 'alert' || view === 'workflow') fetchTemplates();
            if (view === 'dashboard') fetchAnalytics();
            if (view === 'history') fetchHistory();
            if (view === 'teachers') fetchTeachers();
            if (view === 'students') fetchStudents(managementSearch);
            if (view === 'monitor') fetchMonitors();
        }
    }, [view, token, fetchAnalytics, fetchTemplates, fetchHistory, fetchTeachers, fetchStudents, 
        managementSearch, fetchMonitors]); 

    useEffect(() => {
        if (selectedMonitorId) {
            fetchMonitorMatches(selectedMonitorId);
        } else {
            setMonitorMatches([]);
        }
    }, [selectedMonitorId, fetchMonitorMatches]);

    // --- HANDLERS ---
    const handleLogin = (user, receivedToken) => { localStorage.setItem('token', receivedToken); localStorage.setItem('user', JSON.stringify(user)); setToken(receivedToken); setUser(user); };
    const handleLogout = () => { localStorage.removeItem('token'); localStorage.removeItem('user'); setToken(null); setUser(null); setView('dashboard'); };
    const handleViewChange = (event, newValue) => { setView(newValue); };

    // Monitor handlers
    const handleMonitorFieldChange = (e) => {
        const { name, value } = e.target;
        setNewMonitor(prev => ({ ...prev, [name]: value }));
    };

    const handleCreateMonitor = async () => {
        setIsCreatingMonitor(true);
        try {
            const created = await api.createMonitor(newMonitor);
            setSnackbar({ open: true, message: 'Monitor created successfully.', severity: 'success' });
            setNewMonitor({
                name: 'My Monitor',
                imap_host: 'imap.gmail.com',
                imap_port: 993,
                username: '',
                password: '',
                folder: 'INBOX',
                subject_contains: '',
                interval_seconds: 60
            });
            await fetchMonitors();
            setSelectedMonitorId(created.id);
        } catch (err) {
            setSnackbar({ open: true, message: `Failed to create monitor: ${err.message}`, severity: 'error' });
        } finally {
            setIsCreatingMonitor(false);
        }
    };

    const handleDeleteMonitor = async (id) => {
        if (!window.confirm('Delete this monitor?')) return;
        try {
            await api.deleteMonitor(id);
            setSnackbar({ open: true, message: 'Monitor deleted.', severity: 'info' });
            if (selectedMonitorId === id) setSelectedMonitorId(null);
            await fetchMonitors();
        } catch (err) {
            setSnackbar({ open: true, message: `Delete failed: ${err.message}`, severity: 'error' });
        }
    };

    const handleSelectMonitor = (id) => {
        setSelectedMonitorId(id);
    };

    // Workflow handlers
    const processPdf = useCallback(async (selectedFile) => {
        if (!selectedFile) return;
        setIsProcessingPdf(true);
    
        setIntermediateCsv(''); setDisplayData([]); setSnackbar({ open: false, message: '' });
        try {
            const result = await api.uploadPdf(selectedFile);
            setIntermediateCsv(result.csv_data);
            setSnackbar({ open: true, message: 'PDF processed. Ready to list.', severity: 'success' });
      
        } catch (err) { setSnackbar({ open: true, message: `PDF Error: ${err.message}`, severity: 'error' }); } 
        finally { setIsProcessingPdf(false); }
    }, []);
    const handleFileChange = (e) => { const f = e.target.files[0]; setFile(f); processPdf(f); };
    const handleListAll = async () => {
        if (!intermediateCsv) return;
        setIsFetchingDetails(true);
        setSnackbar({ open: false, message: '' });
        try {
            if(templates.length === 0) await fetchTemplates(); 
            const result = await api.fetchStudentDetails(intermediateCsv); 
            if(result.length === 0) {
                setSnackbar({ open: true, message: 'No student details found.', severity: 'warning' });
            }
            setDisplayData(prev => {
                const combined = [...prev, ...result];
                const seen = new Set();
                return combined.filter(item => {
                    if (!item || !item.reg_no) return true;
                    if (seen.has(item.reg_no)) return false;
                    seen.add(item.reg_no);
                    return true;
                });
            });
        } catch (err) { setSnackbar({ open: true, message: `Fetch Error: ${err.message}`, severity: 'error' }); } 
        finally { setIsFetchingDetails(false); }
    };
    const handleListLow = async () => {
       
        if (!intermediateCsv) return;
        setIsFetchingDetails(true);
        setSnackbar({ open: false, message: '' });
        try {
            const sortResult = await api.sortAttendance(intermediateCsv);
            if (!sortResult.sorted_csv_data || sortResult.sorted_csv_data.trim() === 'Reg.No,Subject,Percentage') {
                 setSnackbar({ open: true, message: 'No students <75%.', severity: 'info' }); setIsFetchingDetails(false); return;
            }
           
            if(templates.length === 0) await fetchTemplates(); 
            const fetchResult = await api.fetchStudentDetails(sortResult.sorted_csv_data); 
            if(fetchResult.length === 0) setSnackbar({ open: true, message: 'Low attendance found, but no DB match.', severity: 'warning' });
            setDisplayData(prev => {
                const combined = [...prev, ...fetchResult];
                const seen = new Set();
                return combined.filter(item => {
                    if (!item || !item.reg_no) return true;
                    if (seen.has(item.reg_no)) return false;
                    seen.add(item.reg_no);
                    return true;
                });
            });
        } catch (err) { setSnackbar({ open: true, message: `Fetch Error: ${err.message}`, severity: 'error' }); } 
        finally { setIsFetchingDetails(false); }
    };
    
    // manual entry helpers
    const handleAddManualStudent = () => {
        if (!manualRegNo) return;
        const newEntry = {
            reg_no: manualRegNo,
            name: manualName || '',
            student_email: manualStudentEmail || '',
            parent_email: manualParentEmail || '',
            subjects: []
        };
        setDisplayData(prev => [...prev, newEntry]);
        // clear input fields
        setManualRegNo('');
        setManualName('');
        setManualStudentEmail('');
        setManualParentEmail('');
    };

    const handleRemoveStudentRow = (index) => {
        setDisplayData(prev => prev.filter((_, i) => i !== index));
    };

    const handleClearDisplay = () => {
        setDisplayData([]);
    };

    // Alert Tab Handler
    const handleSendMassAlert = async (payload, attachment) => {
       
        setIsSendingAlert(true);
        setSnackbar({ open: false, message: '' });
        try {
            const result = await api.sendMassAlert(payload, attachment);
            setSnackbar({ open: true, message: `Mass alert sent! ${result.results.success_count} succeeded, ${result.results.fail_count} failed.`, severity: 'success' });
            setIsAlertModalOpen(false);
            fetchAnalytics(); 
        } catch (err) {
            setSnackbar({ open: true, message: `Alert Failed: ${err.message}`, severity: 'error' });
        } finally {
       
            setIsSendingAlert(false);
        }
    };
    
    // Email handlers (for Workflow)
    const handleSendAllEmails = async (payload, attachment) => { setLoading(true); try { const result = await api.sendEmails(payload, attachment); if (result.success) { setSnackbar({ open: true, message: `Email process complete!`, severity: 'success' }); fetchAnalytics(); setIsModalOpen(false); } else { setSnackbar({ open: true, message: `Sending failed: ${result.reason}`, severity: 'error' }); } } catch (err) { setSnackbar({ open: true, message: err.message, severity: 'error' });
        throw err; } finally { setLoading(false); } };
    const handleSendSingleEmail = async (payload, attachment, regNo) => { try { const result = await api.sendEmails(payload, attachment); if (result.success && result.results[0]?.status === 'success') { setSnackbar({ open: true, message: `Email sent to ${regNo}.`, severity: 'success' }); fetchAnalytics(); } else { const reason = result.results[0]?.reason || result.reason; setSnackbar({ open: true, message: `Failed to send to ${regNo}: ${reason}`, severity: 'error' }); } } catch (err) { setSnackbar({ open: true, message: `Failed to 
        send to ${regNo}: ${err.message}`, severity: 'error' }); } };

   
    //const handleOpenTemplateModal = (template = { id: null, name: '', body: '' }) => { setCurrentTemplate(template); setTemplateModalOpen(true); };
   const handleSaveTemplate = async () => { try { await api.saveTemplate(currentTemplate); setTemplateModalOpen(false); fetchTemplates(); setSnackbar({ open: true, message: 'Template saved!', severity: 'success' }); } catch (err) { setSnackbar({ open: true, message: `Save failed: ${err.message}`, severity: 'error' }); } };
   // const handleDeleteTemplate = async (id) => 
  //      { if (window.confirm('Are you sure?')) { try { await api.deleteTemplate(id); fetchTemplates(); setSnackbar({ open: true, message: 'Template deleted.', severity: 'info' }); } catch (err) { setSnackbar({ open: true, message: `Delete failed: ${err.message}`, severity: 'error' }); } } };
    
    // Management Handlers for Both Types
    const handleOpenEditModal = (item, type) => { 
        setCurrentItem({ ...item }); 
        setModalType(type); 
        setEditModalOpen(true); 
    };
    
    const handleSaveItem = async () => { 
   
        setLoading(true); 
        try {
            if (modalType === 'teacher') {
                await api.saveTeacher(currentItem);
                fetchTeachers();
            } else if (modalType === 'student') {
                await api.saveStudent(currentItem);
                fetchStudents(managementSearch);
            }
          
            setEditModalOpen(false);
            setSnackbar({ open: true, message: `${modalType} saved!`, severity: 'success' }); 
        } catch (err) { 
            setSnackbar({ open: true, message: `Save failed: ${err.message}`, severity: 'error' }); 
        } finally {
            setLoading(false);
        }
    };
    
    const handleDeleteTeacher = async (id) => { if (window.confirm('Are you sure?')) { try { await api.deleteTeacher(id); fetchTeachers(); setSnackbar({ open: 
        true, message: 'Teacher deleted.', severity: 'info' }); } catch (err) { setSnackbar({ open: true, message: `Delete failed: ${err.message}`, severity: 'error' }); } } };
    
    const handleDeleteStudent = async (id) => { 
        if (window.confirm('Are you sure you want to delete this student?')) { 
            try { 
             
                await api.deleteStudent(id); 
                fetchStudents(managementSearch); 
                setSnackbar({ open: true, message: 'Student deleted.', severity: 'info' }); 
            } catch (err) { 
                setSnackbar({ open: true, message: `Delete failed: ${err.message}`, severity: 'error' }); 
            } 
        } 
    };

    const handleItemChange = (e) => { const { name, value, type, checked } = e.target; setCurrentItem(prev => 
        ({ ...prev, [name]: type === 'checkbox' ? checked : value })); };

    if (!token) { return <ThemeProvider theme={darkTheme}><CssBaseline /><LoginScreen onLogin={handleLogin} /></ThemeProvider>; }

    // --- RENDER ---
    return (
        <ThemeProvider theme={darkTheme}>
             <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
                 <CssBaseline />
                 <GlobalStyles styles={{
                     body: {
                         background: 'linear-gradient(135deg, #0d1b2a 0%, #07141f 55%, #0b223a 100%)',
                         minHeight: '100vh',
                         backgroundAttachment: 'fixed'
                     },
                     '::-webkit-scrollbar': { width: 10 },
                     '::-webkit-scrollbar-thumb': {
                         background: 'rgba(255,255,255,0.12)',
                         borderRadius: 10
                     }
                 }} />
                 {/* AppBar */}
                 <AppBar position="static" color="default" elevation={1}>
                     <Toolbar>
             
                        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>MonitorMail</Typography>
                        <Link href="https://academia.srmist.edu.in/" target="_blank" rel="noopener noreferrer" color="inherit" sx={{ textDecoration: 'none', mr: 2, '&:hover': { textDecoration: 'underline' }}}>ACADEMIA</Link>
                   
                        <Button color="inherit" onClick={handleLogout}>Logout</Button>
                    </Toolbar>
                 </AppBar>
                 
                
                {/* Main Content */}
                 <Container component="main" sx={{ py: 4, flexGrow: 1 }}>
                     {/* Tabs */}
                    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3, borderRadius: 2, background: 'rgba(255,255,255,0.04)', px: 1, py: 1 }}>
                        <Tabs
                            value={view}
                            onChange={handleViewChange}
                            variant="scrollable"
                            scrollButtons="auto"
                            textColor="primary"
                            indicatorColor="primary"
                            sx={{
                                '& .MuiTabs-indicator': {
                                    height: 4,
                                    borderRadius: 2
                                }
                            }}
                        >
                            <Tab label="Dashboard" value="dashboard" sx={{ textTransform: 'none' }} />
                            <Tab label="Low Attendance" value="workflow" sx={{ textTransform: 'none' }} />
                            <Tab label="Alert/Notify" value="alert" sx={{ textTransform: 'none' }} />
                            <Tab label="Mail Monitor" value="monitor" sx={{ textTransform: 'none' }} />
<Tab label="Templates" value="templates" sx={{ textTransform: 'none' }} />
                            {user.is_admin && <Tab label="Teacher Management" value="teachers" sx={{ textTransform: 'none' }} />}
                            <Tab label="Student Management" value="students" sx={{ textTransform: 'none' }} />
                        </Tabs>
                    </Box>

                     {/* Views */}
                     {view === 'dashboard' && (
                        analytics ? (
                            <>
                                <Paper sx={{ p: 3, mb: 3, borderRadius: 3, background: 'rgba(255,255,255,0.06)', boxShadow: '0 16px 40px rgba(0,0,0,0.35)' }}>
                                    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'flex-start', sm: 'center' }, justifyContent: 'space-between', gap: 2 }}>
                                        <Box>
                                            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                                                Welcome back, {user?.name || user?.email || 'User'}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">\
                                                Here are your latest stats. Use the tabs above to jump to any section.
                                            </Typography>
                                            <Box sx={{ mt: 2 }}>
                                                <Link
                                                    href="/public/gmail-app-password-guide.md"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    sx={{ color: 'primary.main', textDecoration: 'none', fontWeight: 600, '&:hover': { textDecoration: 'underline' } }}
                                                >
                                                    📧 How to Set Up Gmail App Password?
                                                </Link>
                                            </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                            <Button variant="contained" size="small" onClick={() => setView('workflow')}>
                                                <SendIcon sx={{ mr: 1 }} /> Send Notifications
                                            </Button>
                                            <Button variant="outlined" size="small" onClick={() => setView('students')}>
                                                <PeopleIcon sx={{ mr: 1 }} /> Manage Students
                                            </Button>
                                        </Box>
                                    </Box>
                                </Paper>

                                <Grid container spacing={3}>
                                    <Grid item xs={12} md={4}>
                                        <Card sx={{ borderRadius: 3, background: 'rgba(255,255,255,0.04)' }}>
                                            <CardContent>
                                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                    <Box>
                                                        <Typography variant="subtitle2" color="text.secondary">Emails Sent Today</Typography>
                                                        <Typography variant="h3" sx={{ fontWeight: 700 }}>{analytics.emails_sent_today}</Typography>
                                                    </Box>
                                                    <Box sx={{ width: 44, height: 44, bgcolor: 'rgba(77, 208, 225, 0.18)', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                        <SendIcon sx={{ color: 'primary.main' }} />
                                                    </Box>
                                                </Box>
                                            </CardContent>
                                        </Card>
                                    </Grid>

                                    <Grid item xs={12} md={4}>
                                        <Card sx={{ borderRadius: 3, background: 'rgba(255,255,255,0.04)' }}>
                                            <CardContent>
                                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                    <Box>
                                                        <Typography variant="subtitle2" color="text.secondary">Unique Students Contacted</Typography>
                                                        <Typography variant="h3" sx={{ fontWeight: 700 }}>{analytics.unique_students_contacted}</Typography>
                                                    </Box>
                                                    <Box sx={{ width: 44, height: 44, bgcolor: 'rgba(255, 202, 40, 0.18)', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                        <PeopleIcon sx={{ color: 'secondary.main' }} />
                                                    </Box>
                                                </Box>
                                            </CardContent>
                                        </Card>
                                    </Grid>

                                    <Grid item xs={12} md={4}>
                                        <Card sx={{ borderRadius: 3, background: 'rgba(255,255,255,0.04)' }}>
                                            <CardContent>
                                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                    <Box>
                                                        <Typography variant="subtitle2" color="text.secondary">Most Frequent Subject</Typography>
                                                        <Typography variant="h4" sx={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', fontWeight: 700 }}>{analytics.most_frequent_subject}</Typography>
                                                    </Box>
                                                    <Box sx={{ width: 44, height: 44, bgcolor: 'rgba(33, 150, 243, 0.18)', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                        <BarChartIcon sx={{ color: 'info.main' }} />
                                                    </Box>
                                                </Box>
                                            </CardContent>
                                        </Card>
                                    </Grid>

                                    <Grid item xs={12}>
                                        <Paper sx={{ p: 2, borderRadius: 3, background: 'rgba(255,255,255,0.04)' }}>
                                            <Typography variant="h6" sx={{ mb: 1 }}>Top 5 Students by Emails Received</Typography>
                                            <List>
                                                {analytics.top_students.map((s, i) => (
                                                    <React.Fragment key={s.reg_no}>
                                                        <ListItem sx={{ px: 0 }}>
                                                            <ListItemText
                                                                primary={<Typography sx={{ fontWeight: 700 }}>{s.name} <Typography component="span" sx={{ color: 'text.secondary', fontWeight: 500 }}>({s.reg_no})</Typography></Typography>}
                                                                secondary={`Total Emails: ${s.count}`}
                                                            />
                                                            <TrendingUpIcon sx={{ color: 'success.main', ml: 2 }} />
                                                        </ListItem>
                                                        {i < analytics.top_students.length - 1 && <Divider />}
                                                    </React.Fragment>
                                                ))}
                                            </List>
                                        </Paper>
                                    </Grid>
                                </Grid>
                            </>
                        ) : (
                            <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}><CircularProgress /></Box>
                        )
                    )}

                     {view === 'workflow' && ( 
                        <Grid container spacing={3}>
             
                            <Grid item xs={12}>
                                <Paper sx={{ p: 3, borderRadius: 2 }}>
                      
                                    <Typography variant="h5" gutterBottom>Step 1: Select PDF</Typography>
                                    <Typography variant="body2" color="text.secondary" sx={{mb: 2}}>This workflow is specifically for finding and notifying students with low attendance (&lt;75%).</Typography>
      
                                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                       
                                        <Button variant="outlined" component="label" startIcon={<UploadFileIcon />} disabled={isProcessingPdf}>
                                            {isProcessingPdf ? 'Processing...' : 'Select PDF'}
                      
                                            <input type="file" hidden onChange={handleFileChange} accept=".pdf" />
                                        </Button>
          
                                        <Typography variant="body2">{file ? file.name : 'No file selected.'}</Typography>
                                        
                                        {isProcessingPdf && <CircularProgress size={24} />}
                                    </Box>
                                    {intermediateCsv 
                                        && <Typography variant="body2" color="success.main" sx={{mt: 1}}>PDF processed. Ready to list.</Typography>}
                                </Paper>
                            </Grid>
        
                            <Grid item xs={12}>
                                <Paper sx={{ p: 3, borderRadius: 2 }}>
                 
                                    <Typography variant="h5" gutterBottom>Step 2: Fetch Student Details</Typography>
                                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 2 }}>
      
                                        <Button variant="contained" onClick={handleListAll} disabled={!intermediateCsv || isFetchingDetails || isProcessingPdf}>{isFetchingDetails ? <CircularProgress size={24} /> : 'List All Students (from PDF)'}</Button>
                          
                                        <Button variant="contained" onClick={handleListLow} disabled={!intermediateCsv || isFetchingDetails || isProcessingPdf}>{isFetchingDetails ? <CircularProgress size={24} /> : 'List Low Attendance (&lt;75%)'}</Button>
                                    </Box>

                                </Paper>
                            </Grid>

                            <Grid item xs={12}>
                                <Paper sx={{ p: 3, borderRadius: 2, display: 'flex', flexDirection: 'column' }}>
                                 
                                    <Typography variant="h5" gutterBottom>Step 3: Preview and Notify</Typography>

                                    {/* manual entry form */}
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                                        <TextField label="Reg. No" value={manualRegNo} onChange={e => setManualRegNo(e.target.value)} size="small" />
                                        <TextField label="Name (optional)" value={manualName} onChange={e => setManualName(e.target.value)} size="small" />
                                        <TextField label="Student Email" value={manualStudentEmail} onChange={e => setManualStudentEmail(e.target.value)} size="small" />
                                        <TextField label="Parent Email" value={manualParentEmail} onChange={e => setManualParentEmail(e.target.value)} size="small" />
                                        <Button variant="outlined" size="small" onClick={handleAddManualStudent} disabled={!manualRegNo}>Add Student</Button>
                                        <Button variant="text" size="small" color="error" onClick={handleClearDisplay} disabled={displayData.length === 0}>Clear List</Button>
                                    </Box>

                                    {/* table preview */}
                                    <TableContainer component={Paper} sx={{ maxHeight: '400px', mb: 2 }}>
                                        <Table size="small" stickyHeader>
                                            <TableHead>
                                                <TableRow>
                                                    <TableCell>Reg.No</TableCell>
                                                    <TableCell>Name</TableCell>
                                                    <TableCell>Student Email</TableCell>
                                                    <TableCell>Parent Email</TableCell>
                                                    <TableCell>Subjects</TableCell>
                                                    <TableCell align="center">Action</TableCell>
                                                </TableRow>
                                            </TableHead>
                                            <TableBody>
                                                {(displayData.length === 0) ? (
                                                    <TableRow>
                                                        <TableCell colSpan={6} align="center">{!intermediateCsv && !displayData.length ? "Please select a PDF or add students manually." : isFetchingDetails ? "Fetching student data..." : "No students to display."}</TableCell>
                                                    </TableRow>
                                                ) : (
                                                    displayData.map((student, idx) => (
                                                        <TableRow key={idx}>
                                                            <TableCell>{student.reg_no || 'N/A'}</TableCell>
                                                            <TableCell>{student.name || 'N/A'}</TableCell>
                                                            <TableCell>{student.student_email || 'N/A'}</TableCell>
                                                            <TableCell>{student.parent_email || 'N/A'}</TableCell>
                                                            <TableCell style={{whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 200}}>{Array.isArray(student.subjects) && student.subjects.length > 0 ? student.subjects.map(s => s.Subject || s.course_title || '').join(', ') : '-'}</TableCell>
                                                            <TableCell align="center"><IconButton size="small" onClick={() => handleRemoveStudentRow(idx)}><CloseIcon fontSize="small" /></IconButton></TableCell>
                                                        </TableRow>
                                                    ))
                                                )}
                                            </TableBody>
                                        </Table>
                                    </TableContainer>

                                    <Button variant="contained" color="secondary" onClick={() => setIsModalOpen(true)} disabled={displayData.length === 0 || isFetchingDetails || isProcessingPdf} sx={{ mt: 0, alignSelf: 'flex-start' }}>Mail / Notify Selected Students</Button>
     
                                </Paper>
                            </Grid>
                      
                        </Grid>
                     )}

                     {view === 'alert' && ( 
    
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h5" gutterBottom>Mass Alert / Notification</Typography>
                    
                            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                                This tool will send an email to every student in the database.
                    
                                You can use templates for personalization (e.g., [Student Name]).
                            </Typography>
                            <Button 
 
                                variant="contained" 
                                color="secondary" 
           
                                onClick={() => setIsAlertModalOpen(true)}
                                disabled={isSendingAlert}
                      
                            >
                                {isSendingAlert ? <CircularProgress size={24} /> : 'Compose Mass Notification'}
                            </Button>
   
                        </Paper> 
                     )}

                     {view === 'monitor' && (
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h5" gutterBottom>Email Monitor</Typography>
                            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                                Create a monitor that checks an IMAP inbox for new messages containing a keyword in the subject, and logs matches for review.
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <Paper sx={{ p: 2, mb: 2 }}>
                                        <Typography variant="subtitle1" gutterBottom>Create new monitor</Typography>
                                        <TextField label="Monitor Name" name="name" value={newMonitor.name} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <TextField label="IMAP Host" name="imap_host" value={newMonitor.imap_host} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <TextField label="IMAP Port" name="imap_port" type="number" value={newMonitor.imap_port} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <TextField label="Email Address" name="username" value={newMonitor.username} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <TextField label="Email Password" type="password" name="password" value={newMonitor.password} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <TextField label="Folder" name="folder" value={newMonitor.folder} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <TextField label="Subject contains" name="subject_contains" value={newMonitor.subject_contains} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} helperText="Keyword to match the email subject." />
                                        <TextField label="Poll interval (seconds)" name="interval_seconds" type="number" value={newMonitor.interval_seconds} onChange={handleMonitorFieldChange} fullWidth sx={{ mb: 2 }} />
                                        <Button variant="contained" onClick={handleCreateMonitor} disabled={isCreatingMonitor}>
                                            {isCreatingMonitor ? <CircularProgress size={24} /> : 'Create Monitor'}
                                        </Button>
                                    </Paper>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <Paper sx={{ p: 2, mb: 2 }}>
                                        <Typography variant="subtitle1" gutterBottom>Monitors</Typography>
                                        {monitorLoading ? <CircularProgress /> : (
                                            monitors.length === 0 ? (
                                                <Typography color="text.secondary">No monitors configured yet.</Typography>
                                            ) : (
                                                <List>
                                                    {monitors.map(m => (
                                                        <ListItem key={m.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 1 }}>
                                                            <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                                <Typography variant="subtitle2">{m.name}</Typography>
                                                                <Box>
                                                                    <Button size="small" onClick={() => handleSelectMonitor(m.id)} sx={{ mr: 1 }}>
                                                                        {selectedMonitorId === m.id ? 'Selected' : 'View'}
                                                                    </Button>
                                                                    <Button size="small" color="error" onClick={() => handleDeleteMonitor(m.id)}>Delete</Button>
                                                                </Box>
                                                            </Box>
                                                            <Typography variant="body2" color="text.secondary">{m.username} @ {m.imap_host}:{m.imap_port} • "{m.subject_contains}"</Typography>
                                                            <Typography variant="body2" color="text.secondary">Interval: {m.interval_seconds}s {m.last_checked ? `• last checked ${new Date(m.last_checked * 1000).toLocaleString()}` : ''}</Typography>
                                                        </ListItem>
                                                    ))}
                                                </List>
                                            )
                                        )}
                                    </Paper>
                                    {selectedMonitorId && (
                                        <Paper sx={{ p: 2 }}>
                                            <Typography variant="subtitle1" gutterBottom>Matches</Typography>
                                            {monitorMatches.length === 0 ? (
                                                <Typography color="text.secondary">No matches yet.</Typography>
                                            ) : (
                                                <List>
                                                    {monitorMatches.map((match, idx) => (
                                                        <ListItem key={idx} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                                                            <Typography variant="body2"><strong>{match.subject}</strong></Typography>
                                                            <Typography variant="body2" color="text.secondary">From: {match.from}</Typography>
                                                            <Typography variant="body2" color="text.secondary">{new Date(match.timestamp).toLocaleString()}</Typography>
                                                            <Typography variant="body2" sx={{ mt: 1 }}>{match.snippet}</Typography>
                                                            <Divider sx={{ my: 1, width: '100%' }} />
                                                        </ListItem>
                                                    ))}
                                                </List>
                                            )}
                                        </Paper>
                                    )}
                                </Grid>
                            </Grid>
                        </Paper>
                     )}

                     {view === 'history' && (
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h5" gutterBottom>Communication History</Typography>
                            <TextField fullWidth label="Search by Registration No. or Name" value={historySearch} onChange={e => { setHistorySearch(e.target.value); fetchHistory(e.target.value); }} sx={{ mb: 2 }} />
                            {history.map(h => (
                                <Paper key={h.id} variant="outlined" sx={{ p: 2, mb: 2 }}>
                                    <Typography variant="subtitle1"><strong>To:</strong> {h.student_name} ({h.student_reg_no})</Typography>
                                    <Typography variant="body2" color="text.secondary"><strong>Recipients:</strong> {h.recipients}</Typography>
                                    <Typography variant="body2" color="text.secondary"><strong>Sent By:</strong> {h.teacher_email} on {new Date(h.sent_at).toLocaleString()}</Typography>
                                    <TextField multiline fullWidth readOnly value={h.body} sx={{ mt: 1, bgcolor: '#222', '.MuiInputBase-input': { fontFamily: 'monospace' } }} />
                                </Paper>
                            ))}
                            {history.length === 0 && <Typography color="text.secondary" sx={{mt: 2}}>No history found matching your search.</Typography>}
                        </Paper>
                     )}
                     {view === 'teachers' && user.is_admin && ( 
      
                        <Paper sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}><Typography variant="h5">Teacher Management</Typography><Button variant="contained" onClick={() => handleOpenEditModal({name: '', email: '', password: '', is_admin: false}, 'teacher')}>Add New Teacher</Button></Box>
 
                            <TableContainer><Table size="small"><TableHead><TableRow><TableCell>Name</TableCell><TableCell>Email</TableCell><TableCell>Admin Status</TableCell><TableCell align="right">Actions</TableCell></TableRow></TableHead><TableBody>{teachers.map(t => (<TableRow key={t.id}><TableCell>{t.name}</TableCell><TableCell>{t.email}</TableCell><TableCell>{t.is_admin ? 'Yes' : 'No'}</TableCell><TableCell align="right"><Button size="small" onClick={() => handleOpenEditModal(t, 'teacher')}>Edit</Button><Button size="small" color="error" disabled={t.id === user.id} onClick={() => handleDeleteTeacher(t.id)}>Delete</Button></TableCell></TableRow>))}</TableBody></Table></TableContainer>
                        </Paper> 
 
                     )}

                     {view === 'templates' && (
                        <Paper sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                                <Typography variant="h5">Email Templates</Typography>
                                <Button 
                                    variant="contained" 
                                    onClick={() => { setCurrentTemplate({ id: null, name: '', body: '' }); setTemplateModalOpen(true); }}
                                >
                                    New Template
                                </Button>
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Design reusable email templates. Use <code>[Student Name]</code> and <code>[Subject List]</code> placeholders.
                            </Typography>
                            {templates.length === 0 ? (
                                <Paper sx={{ p: 4, textAlign: 'center' }}>
                                    <Typography color="text.secondary">No templates yet. Create your first one!</Typography>
                                </Paper>
                            ) : (
                                <TableContainer>
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Name</TableCell>
                                                <TableCell>Preview</TableCell>
                                                <TableCell width={120}>Actions</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {templates.map((template) => (
                                                <TableRow key={template.id}>
                                                    <TableCell>{template.name}</TableCell>
                                                    <TableCell sx={{ maxWidth: 400 }}>
                                                        <Typography variant="body2" noWrap sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                                                            {template.body.substring(0, 100)}...
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Button 
                                                            size="small" 
                                                            onClick={() => { setCurrentTemplate(template); setTemplateModalOpen(true); }}
                                                        >
                                                            Edit
                                                        </Button>
                                                        <Button 
                                                            size="small" 
                                                            color="error" 
                                                            sx={{ ml: 1 }}
                                                            onClick={async () => {
                                                                if (window.confirm('Delete this template?')) {
                                                                    try {
                                                                        await api.deleteTemplate(template.id);
                                                                        fetchTemplates();
                                                                        setSnackbar({ open: true, message: 'Template deleted.', severity: 'info' });
                                                                    } catch (err) {
                                                                        setSnackbar({ open: true, message: `Delete failed: ${err.message}`, severity: 'error' });
                                                                    }
                                                                }
                                                            }}
                                                        >
                                                            Delete
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            )}
                        </Paper>
                     )}

                     {view === 'students' && ( 
                        <Paper sx={{ p: 3 }}>
   
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="h5">Student Management</Typography>
        
                                <Button variant="contained" onClick={() => handleOpenEditModal({reg_no: '', name: '', section: '', department: '', phone_number: '', email: '', parent_mobile: '', parent_email: ''}, 'student')}>Add New Student</Button>
                            </Box>
   
                            <TextField 
                                fullWidth 
                  
                                label="Search by Name or Registration No." 
                                value={managementSearch} 
                        
                                onChange={e => setManagementSearch(e.target.value)} 
                                onBlur={() => fetchStudents(managementSearch)} 
                               
                                onKeyPress={(e) => e.key === 'Enter' && fetchStudents(managementSearch)} 
                                sx={{ mb: 2 }} 
                            />
     
                            <TableContainer><Table size="small"><TableHead><TableRow><TableCell>Reg.No</TableCell><TableCell>Name</TableCell><TableCell>Email</TableCell><TableCell>Parent Email</TableCell><TableCell align="right">Actions</TableCell></TableRow></TableHead><TableBody>
                                {loading ? <TableRow><TableCell colSpan={5} align="center"><CircularProgress /></TableCell></TableRow> :
             
                                    students.map(s => (<TableRow key={s.id}><TableCell>{s.reg_no}</TableCell><TableCell>{s.name}</TableCell><TableCell>{s.email || 'N/A'}</TableCell><TableCell>{s.parent_email || 'N/A'}</TableCell><TableCell align="right"><Button size="small" onClick={() => handleOpenEditModal(s, 'student')}>Edit</Button><Button size="small" color="error" onClick={() => handleDeleteStudent(s.id)}>Delete</Button></TableCell></TableRow>))
                                }
        
                            </TableBody></Table></TableContainer>
                        </Paper> 
                     )}

           
                </Container>
                 
                 {/* Footer */}
                 <Box component="footer" sx={{ bgcolor: 'background.paper', p: 3, mt: 'auto', borderTop: '1px solid', borderColor: 'divider' }}> 
   
                    <Container maxWidth="lg">
                        <Typography variant="body2" color="text.secondary" align="center">Contact for support:</Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'center', 
                            alignItems: 'center', gap: 2, mt: 1 }}>
                            <MailOutlineIcon fontSize="small" /><Typography variant="body2">ujjwal3rd@gmail.com</Typography>
                            <PhoneIcon fontSize="small" sx={{ ml: 2 }}/><Typography variant="body2">+91 8210052876</Typography>
     
                        </Box>
                    </Container>
                 </Box>
             </Box>
        
             {/* Workflow Email Modal */}
             <EmailModal open={isModalOpen} onClose={() => setIsModalOpen(false)} data={displayData} onSendAll={handleSendAllEmails} onSendSingle={handleSendSingleEmail} loading={loading} templates={templates} title="Review & Send Emails" user={user} setDisplayData={setDisplayData} setSnackbar={setSnackbar} />
             
             

             {/* Mass Alert Modal */}
             <MassAlertModal 
                open={isAlertModalOpen} 
                onClose={() => setIsAlertModalOpen(false)} 
 
                onSend={handleSendMassAlert}
                loading={isSendingAlert} 
                templates={templates}
                user={user}
             />

             {/* Template Modal */}
             <Modal open={templateModalOpen} onClose={() => setTemplateModalOpen(false)} closeAfterTransition BackdropComponent={Backdrop} BackdropProps={{ timeout: 500, sx: { backgroundColor: '#000' } }}>
                  <Fade in={templateModalOpen}>
                     <Box sx={editModalStyle}>
    
                        <Typography variant="h6" gutterBottom>{currentTemplate.id ? 'Edit' : 'Create'} Template</Typography>
                        <TextField fullWidth label="Template Name" value={currentTemplate.name} onChange={e => setCurrentTemplate({...currentTemplate, name: e.target.value})} sx={{ mb: 2 }} />
            
                        <TextField fullWidth multiline rows={10} label="Template Body" value={currentTemplate.body} onChange={e => setCurrentTemplate({...currentTemplate, body: e.target.value})} helperText="Use [Student Name] and [Subject List] as placeholders." />
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}><Button onClick={() => setTemplateModalOpen(false)}>Cancel</Button><Button variant="contained" onClick={handleSaveTemplate}>Save Template</Button></Box>
     
                    </Box>
                 </Fade>
             </Modal>
             
             {/* Management Edit Modal (for BOTH types) */}
             <Modal open={editModalOpen} onClose={() => setEditModalOpen(false)} closeAfterTransition BackdropComponent={Backdrop} BackdropProps={{ timeout: 500, sx: { backgroundColor: '#000' } }}>
                  <Fade in={editModalOpen}>
                     <Box sx={{...editModalStyle, overflowY: 'auto'}}> 
 
                        <Typography variant="h6" gutterBottom>{currentItem?.id ? 'Edit' : 'Add'} {modalType}</Typography> 
                        {currentItem && modalType === 'teacher' && ( 
              
                            <Grid container spacing={2} sx={{mt: 1}}>
                                <Grid item xs={12}><TextField name="name" label="Full Name" value={currentItem.name || ''} onChange={handleItemChange} fullWidth/></Grid>
                 
                                <Grid item xs={12}><TextField name="email" label="Email" value={currentItem.email || ''} onChange={handleItemChange} fullWidth/></Grid>
                                <Grid item xs={12}><TextField name="password" label={currentItem.id ? "New Password (optional)" : "Password"} type="password" onChange={handleItemChange} fullWidth helperText={currentItem.id ? "Leave blank to keep current password" : ""}/></Grid>
                                <Grid item xs={12}><FormControlLabel control={<Checkbox name="is_admin" checked={currentItem.is_admin || false} onChange={handleItemChange} />} label="Is Admin"/></Grid>
                            </Grid> 
   
                        )}
                        {currentItem && modalType === 'student' && ( 
                         
                            <Grid container spacing={2} sx={{mt: 1}}>
                                <Grid item xs={12} sm={6}><TextField name="reg_no" label="Reg.No" value={currentItem.reg_no || ''} onChange={handleItemChange} fullWidth/></Grid>
                            
                                <Grid item xs={12} sm={6}><TextField name="name" label="Name" value={currentItem.name || ''} onChange={handleItemChange} fullWidth/></Grid>
                                <Grid item xs={12} sm={6}><TextField name="section" label="Section" value={currentItem.section || ''} onChange={handleItemChange} fullWidth/></Grid>
                     
                                <Grid item xs={12} sm={6}><TextField name="department" label="Department" value={currentItem.department || ''} onChange={handleItemChange} fullWidth/></Grid>
                                <Grid item xs={12} sm={6}><TextField name="phone_number" label="Phone Number" value={currentItem.phone_number || ''} onChange={handleItemChange} fullWidth/></Grid>
             
                                <Grid item xs={12} sm={6}><TextField name="email" label="Email" value={currentItem.email || ''} onChange={handleItemChange} fullWidth/></Grid>
                                <Grid item xs={12} sm={6}><TextField name="parent_mobile" label="Parent Mobile" value={currentItem.parent_mobile || ''} onChange={handleItemChange} fullWidth/></Grid>
     
                                <Grid item xs={12} sm={6}><TextField name="parent_email" label="Parent Email" value={currentItem.parent_email || ''} onChange={handleItemChange} fullWidth/></Grid>
                            </Grid> 
          
                        )}
                        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 1 }}><Button onClick={() => setEditModalOpen(false)}>Cancel</Button><Button variant="contained" onClick={handleSaveItem} disabled={loading}>{loading ? <CircularProgress size={24}/> : 'Save Changes'}</Button></Box>
                 
                    </Box>
                 </Fade>
             </Modal>

             {/* Snackbar */}
             <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={() => setSnackbar({ ...snackbar, open: false })} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' 
                }}><Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} sx={{ width: '100%' }}>{snackbar.message}</Alert></Snackbar>
        </ThemeProvider>
    );
}

export default App;
