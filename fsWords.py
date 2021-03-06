#!/usr/bin/env python -B

import sys
import re
import os.path
import os
import socket
import string
import threading
import Queue
import tempfile
import random
import shutil
import time
import hashlib
import cStringIO
import stat
import calendar
import cStringIO
import cPickle

kWordTablePacked= "@@AfBNCKDHEFFJGFHQIRJBKBLHMLNGOTPIQARESTTzUFVBWQXAYEZA;A@LAABCCCDBEAFBGCHAIAJAKALJMCNzPAQARFSGTCUAVAWAXAYAZA;B@AAGDAEzIBLDOHRLUQYK;C@AAeEDHPIFLENAOzREUEYAZA;D@JAcEzIqLAMAOnRLSAUHWDYA;E@AAcBACADDEAFDGFHAIIJAKALJMMNnOAPEQERDSJTFUDVzWAXpYHZA;F@AATEGINLEOzRTUD;G@AAKEJHAIMLDNAOzRcUCYA;H@AAuEzIrOQUDYA;I@YAABACADAEAFFGAIAJAKALAMDNzOAPARASYTXUAVAWAXAZA;J@AAQEzIAOgRAUq;K@AACEMHAIzNjOAUA;L@AAlBADAEYIaLCNAOzTAUBYA;M@AAzEjIPMANAOfRATAUKYW;N@AAJDAETICNAOzTAUCYA;O@BAABACADAEAFzGAHAIALAMANGPARESATCUEVBWBXAYAZA;P@AAdEeFAHDIDLMNAOPPARzSATAUKYA;QQARATAUz;R@AAHDAEzHAILNAOJSATAUDYA;S@JAkBACEEdHzIPKALDMDNAOjPMQARATUUQWDYB;T@AABEAHzIALAOJRBUAWAYA;U@ABACADAEAGAKALAMANzOAPeRASKTBZA;V@AAkEzIjOTSAUA;W@AAWEXHzIoMAORRC;X@zAIIiXR;Y@AAAEjIAOzTAUA;ZAgEzImOMUC;;AA@ABACWDBHAIAKALWMMNYPARzSITAVAZD;B@HAEBEDAEHHAITJALvMANAOzRHSETAUDYEZA;C@BAABDClDBEzHcICKOLFOIQDRFTcUEYA;D@zADBACADCEWFAGAHAIDJALAMBNBOBRASCTAUBVFWAYE;E@AABCADAGALzMANAOARBSFTAUA;F@BABEGFWIALANAOARFTz;G@BAzBADAErGBIFLAMANBOIPARDSATAUC;H@zAGBADAECHAIBJAKALAMANAOAPARASATAUAZA;I@BABCADcEAGAJALFMCNzOARESETMUAXAZA;JADEyIAOz;K@LAABAEzFAHAIEKALANAOARASATAUAYA;L@MABBACADAEDFAGAHAICKBLzMENAOBPARASGTGUBVAWBYAZA;M@WALBDEzGAHAIGLAMCNAONPDRASBTAUBYAZA;N@JAABACCDzEAFAGBHAIBJAKALAMANBOAQARASBTDUAVAWAXAYCZA;O@ACADBHzLEMENBRXSATB;P@JAFBAETHJIXKALAMANBOIPzRASPTmUBWA;QUz;R@nAFBACDDVEzFAGEHAIMJAKJLEMINDOEPAQARKSLToUAVBWAYIZA;S@zAABACADAEGGAHCIDKBLAMANAOBPAQARASNTQUCYA;T@zAACAEKFAHMIKLAMANAOARASATCUBWAYA;U@BBACADEEAGXLLMANCPARASzTIVAXA;V@AAAEzIHOCSAUAYA;W@zAnBBDAEBFCGAHAIAKALAMANEOARASFTAYB;X@zAFDAEqIDLAOA;Y@zAABADAEDFAHAIHLAMAOAPARASJTAUAWA;Z@cAzBAEVGAIcLAMBNAOGRBUAYCZG;;BA@EAGBWCXDJEAFAGBHCICJAKCLSMANzOAPMRgSRTYUAVAWAYBZA;B@DAzEiIHLKOMSAUAYB;COz;DACEDIiOIUz;E@zAGBACKDCEKFJGFHKIEKALGMANDOAPAQARKSETFUAVAWAYBZA;GOz;HAFEAOz;I@AAHBACADOEAGCHAJALOMENMODQARHSDTzUAZA;JEzOAUA;LADEzIQOKUAYE;MAGDAEBIz;NAWEzIJOC;O@AAFBACADJEAGAHAIAKALCMDNHOHRQSBTTUzVHWFXAYBZA;R@AAdEtIrOzUHYA;S@oANCIEzHCIcOJTYUG;T@zAjEHFEIDLEOGSL;UBACADAEAFAGAIDKALCMANBRISDTzYBZA;VENIz;WEz;Y@zAAEAHALBRASATAWA;ZAzEo;;CA@GAABACADAEDFAGAHAIBKALcMzNqOAPXRXSdTQUpVAWAYA;BEz;CAMEMHAIBLAOzRASAUL;DABOAUz;E@zABBADDECFAIELBMANEPCRGSMTAUAVAZA;H@zAKBACAEHFAIKLAMANAOCPARCSATAUBWAYAZA;I@AAPBACADCEjFEGALEMANIONPTROSPTzUCVEZA;K@zAABACAEUFAGAICKALDMANCOBPASJTAWAYA;LAdEzIGOgUKYA;N@ZCZIz;O@AABBCCADAEAFAGAHAIBLEMzNmOAPBRPSATBUbVFWAXAYAZA;QUz;R@AAIEzIiOLUEYK;S@zSATE;T@sACEQFAIzLFMANAOFRESKUXYA;U@ABICADAEAFAIALzMUNDOAPHRhSXTYUA;Y@zAACADAIALAMANAPBRBSATA;ZAzEz;;DA@BAABCCADAEAFAGCHLIDKALBMINOPARLSATDULVOWAYzZA;BAzEmImOZRm;CAzHfLDOX;D@LAFEzHAIjLVOIRDSFUCYC;E@qAVBCCIDTEIFFGCHAIAJAKALJMHNPOAPHQARzSgTEUAVFWAXAZA;FAZEEOFUz;G@AAAEzICMTOAUA;HAEEiIqOz;I@AAIBACEDqESFNGCJAKALDMDNzOCPARESjTMUAVIWAXAZA;JADOJUz;KABEzID;LABEzIGOQYu;MAJEzISNAOCTAUA;N@BAAEzGAIB;O@zBACCDAEHFAGCHAICKALDMXNVOFPARBSCTIUGVBWdXAZA;PHzIzOz;R@AAJEzIMOIUDYB;S@zAAEAHAIAMAOAPATFUA;THzICUA;U@AAICzDAEEFCGAIAKHLEMBNCOAPARMSPTNUA;VAzEQIEOA;WADEzIDOARA;Y@zBAEAIALAMASAWA;;EA@JBACHDQFAGAHAIAKHLIMBNGPCRzSSTjUAVIZA;B@NAtBBEzIFLINBOJRWSATkUwYl;C@AAmCAEkHIIKKELFNAOcRGSATzUIYA;D@zAACADAEAFAGAICLAMANAOARASATAUAWAYA;E@zAABACBDSFAHAIBKFLDMGNePMRBSETJVAWAZA;F@GAAEDFEIDLAOzRBSATEUDYA;G@CAzELGDHAIWLEMANAODRLSBUNYX;H@DACDAEGGAIEOzUB;I@AAAEAFAGNIALAMANKPARzSATMUAVGXAYAZA;JAAELOzUD;K@zAEEOIULBNBOBRBSGUAYA;L@zAJBACBDOEMFWGAHAIeKALyMANAOIPDRASKTEUAVPWAYQZA;M@zAFBFDAEKIEJALAMANBODPJRASFUAYA;N@zACBACHDHEFFAGCHAIBJAKALAMANAOAPAQARASDTgUBVAWAYAZA;O@BCADAFLGALAMANGPzRAULVC;P@SAQCAEMFAHzIELCMANAOCPARFSCTOUCYA;Q@ANAUz;R@zADBACCDAEbFAGAHAIFJAKALAMANDOAPAQARASKTCUBVDWAXAYFZA;S@zAABACADAEHFAHBICKALAMANAOAPBQARASTTRUCYA;T@qACBACCEFFAHzIELAMANAOBPARCSETFUEWDYC;U@PBHCADCEBFALAMBNiOAPDRzSMTEXAZA;V@AAAEzIIOBUAYA;W@zAGBACADAEKFAHFIKLAMANBOBRASJTAYA;X@EAQCrEUHCILLAMAOAPzQASATXUAYA;Y@zAABACAEDHAIALAMANAOASATA;Z@HAGBAEzIILANAOBRYUAVAZR;;FA@ABACgDAGAIfLUMNNDRTSHTzUCVGWAXAYA;CLz;DIz;E@bAUBACNDBEKFAGAIBLKMANHPARzSGTCUBVAWE;F@OABDAEzHAINLENAOFRASAUA;HEz;IAABACiDCEXFKGGKALQNiRzSDTXVMXC;LANEzIUOmUKYJ;NEz;OAACADAEAGAHAIALBNAOBPARzSAUDWAXA;PEz;RAFEIIEOzUDYA;S@zAOCBPL;T@TAAEzHDIALAMANASCTAYE;UCADAEAGBLzMANFRJSETB;WARIz;Y@zEAII;;GA@AAABACADBGBHAIzLFMANKOAPARLSATXUAVIWAYAZA;BAEEqIELz;DABIAOz;E@zABBADNEAFAHAIALGMCNbODRTSSTYUAWAZA;FLzUa;G@GATEzIHLROCRESCYA;H@PAABBEBFAIALAMANAOCRASATzWAYA;I@AAABCCADCECFDGAHALDMANYOCPARCSCTAUAVzZA;KIz;LAzEeIROuUAYl;MABEzIANASA;N@zAEEOIQMAOHSFTA;O@YABBADzECGAIBLJMANEOWPARASBTCUAVEWAZA;PAFIILz;RAOEzIDOIUAYB;S@zBAHATAUA;THzIAOARA;U@AARBADAEzIgLYMDNEOARDSCTD;VAz;WIz;Y@NLAMANAPzVA;;HA@AAABBCADIEAFAGAHAIAKALWMCNMOAPCRDSFTzUAVPWAXAYAZA;BAEEBIBOzUA;CAIHILCOVRz;DAEEBIBOPRz;E@zACBACADAEBFAGAHAIDKALAMENDOAPAQARLSBTAUAVAWAXAYFZA;FAAUz;GAIIzLB;HAIENOzUA;I@GAABACbDBECFAGCHAJAKALJMXNROAPCRCSzTDUAVAZA;JAJEzIC;KAQEaUz;LAIEcIEOCYz;MAdEzIBNAOCUA;N@zABERIFOAUA;O@LAABACADAEAGAHAIAKALRMFNCOBPBRFSOTAUzVAWHZA;PAlEzHRIlON;QUz;RAFEzIYOmUBYA;S@zAEEAHFIAOBTZ;T@zAACAEMFAGAHAIALAMANAOAPASCTAUAWAYD;U@CAGBACADAEAFAGAHAIAJAKALBMMNgPARUSzTEVAZA;VAz;WAzHAIEOARA;Y@zAABADAEAGAIALAMANAPARASD;ZAFEWInOFUz;;IA@eBCCADBEAGLHzIAKBLUMFNhPARHSETLVA;B@EACBBEzHAIOLhMANBOBRGSAUXYAZA;C@EAFCAETHzIDKGLANAOARASATCUDYA;D@zAABADBERGAHAIBKALANAOBRASDUBWAYA;E@HCCDSFHGAHAKALHMANRRFSzTIUAVJWAZA;F@zAAEXFPIMLAOARATOUCYE;G@AAADAEDGAHzIBLAMANLOARASATAUAVAYA;HAzIDOvUT;I@zIXMATA;JAzEAOA;K@AAAEzHAIAKALANAVA;L@MABBACADQEKFAGAHAIHKALzMANAOBPARASBTDUAVEYF;M@zADBAESFAGAHAICLAMCNAOBPJRASFUAYAZA;N@zACBACEDHEKFAGuHBIDJAKBLAMANBOAQARASHTJUBVAWAXAYA;O@FBACADAEAGALAMANzPARBSATAUD;P@zATBAEJFAHSIALvMBOBPTRASVTPUCWA;QOAUz;R@zABCCDDEOGAHAIFJAKALAMANAOBPARASITDUAVAYAZA;S@zAABACBDAEFFAGAHEIBJAKALAMANAOAPAQARDSBTFUAYA;T@zAGCAEKFAHtIHLAMANAOARASFTEUCXAYMZA;UDAGAMHNARASz;V@AADEzIJOARAUAYA;WAzIOOE;X@zAAEMIBPESATj;Y@z;Z@EAHEzHAICJAKAOAPDRASATAUAZC;;JA@AABBDCzDBEAGAHOIBKALAMVNCPCQFRJSCTCUAVBWBXAYAZA;E@AAFBBCcDBEAFAGAHMIAKALAMANAOAPBRvSzTAUAWRZC;IBIDIGzLRMiPZRITI;OAQBJCAEBGAHVIzKBLANNPBRZSuTDUWVBWAYuZB;R@z;UAABACADzGAIALEMANAPARCSQTAVA;;KA@AAABIDJGAHOIALBMHNIRKSATzXAZA;BAREFIWOLUz;CLzRB;DEz;E@zBADMEHFAHAIALCMANPPCRCSETKWBYAZA;FAfECOEUz;GRz;HAXEJIEOz;I@AACBACADAEAIAJALDMANzPARASBTA;KAIEzIaOKUd;LAIEzILOBYt;MAfEz;NABELIAOzUA;O@AAEBADCHUICKALGNzOBRZSDTAWAZC;POz;RAEOfUz;S@zAAEAGAHAIAKALAMAOATAYA;T@RAzEIHZOR;UBSKGLsMzPESCTC;VAz;WAzHAOA;Y@zABIB;;LA@CAABNCSDGEAFAGCHBIMKALAMRNzOAPARNSITTUEVBWKXAYJZA;B@BAYEzICOcSCUC;CAGECHhIBOzRAUE;D@zAABACAEEHAIBLANAOARGSBWAYA;E@zALBACBDNECFBGBHAIAKALAMFNGOAPARDSSTLUAVCWBXAYAZA;F@zAAEAIELAPASATAUAWAYA;GAzEYIEOCRQUC;HAzEGIGNBODUB;I@CAVBJCbDBEuFdGdHAIAJBKnLCMFNzOMPGQBRASfTlUBVtXAYAZD;K@zACEUIJOASEYA;L@zAABADAEEFAICMANAOCPASAUAWAYD;M@DAzEBIBLANAOKSAUAYA;N@EACDAEzOAUA;O@CABBACDDAEAFAGAHAIAKALAMCNMOJPAQARzSETEUEVJWLYF;P@zADELFCHFIGLBOASDTAUC;REzIAOCUBYA;S@zAAEIHAIAOuPATBUAYA;T@zAGEGHIIQLAMANAOFPARASBUCYD;U@AADBBCVDIEzGAHAIBKALAMHNIOAPARFSiTOXDZA;V@AAEEzIA;WAzICOARA;Y@zBACADAGAIAMAOARASATAZA;ZAXEz;;MA@IAABACCDJEAGCHAIFJAKJLEMANzOAPARISETEUAVAWAXAYNZA;B@LACEzIFLSOARESDUB;CIz;D@zAzIzMz;E@zADBACADDEAFAGAHAIAJAKALBMBNTOAPAQARGSFTEUAVAWAXAZA;FEAICOzRAUA;G@RAzIz;H@AAFEAIzODUB;I@AADBACBDGEGGWHAJAKALOMANzOEPARCSMTNUAXAZA;JUz;LAzEqIOODYF;M@AAyDAEgIMLAOzPAUEYA;N@aAzEYIRLAMAOHPASBTAUBYA;O@AABBACADGEAGAHAIAKALAMANzOCPARuSeTKUPVEWAZA;P@HAWETHBIDLzOYROSBTTUD;R@zAGECIJOESAWA;S@lBACADAEzHAIAOBPATGUA;T@zAFHUIP;U@AAACzDAEFFAGBLYMANDPARKSyTDZA;VEZIz;WEHOz;Y@zRASCTA;ZIzOzUZ;;NA@OADBGCHDBEAGFHDICKCLRMbNTOAPBRKSDTzUAVDWAYEZA;BAGEzIBLCOFRHUN;C@AABEzHDIGLDODRETCUAYC;D@zAABAECFAGAHAIAKALAMANAOAPARASBTAUAWAYA;E@zADBACEDPECFAGBHAIGJAKALAMCNBOAPMQARMSYTCUAVEWEXAYGZA;FAIEzIyLWOnRCUO;G@zAABADAEFFAGAHAIAKALCMANAOAPARBSHTBUAWAYA;HAzEhIBOBUA;I@KAHBACIDAERFGGTHAIAJAKALAMCNzOQPAQJRASYTfUDVDXAZC;JAzEDOrUk;K@zAAEGFAHAIHLCNBRBSNWAYA;LACEFIBOBUAYz;MAGBADAEzIBLANAOBUA;N@AAFEzIOOfSAURYD;O@NAABACADAEAGAHAIALAMANCOAPARGSATzUCVAWVXAYAZA;PAFELHAIKLGOFRzTBUG;QUz;RAHESIzOFUEYm;S@zABCBEKFAGBHAIIKALAMANAOBPBSATVUEWFYA;T@zAGBAEOFAHDIOLEMANAOxRJSMUBWAYDZA;U@AApBACBEwFjGAIGLAMzNCOAPARLSCTF;VACEzIQOEUAYF;WAzEUHGISOTRA;X@EIz;Y@zAABACAIAMAOASATAWAXA;ZADIBOzYD;;OA@EBjCbDuFAGAHRIAKFLMMTNLPBReSjTzVDXAZC;B@zAcBKDAEeGAIEJJLiNAOMRASaTNUAVBWA;C@AACCTDAEHHCILKzLCOARCTGUCYA;D@zAABACADAECFAGAHAIDKALAMANAOAPARASFTAUHWAYC;E@OBACADAFAGAHAIALBMANARESzTUVrZA;F@zAACAEAFBIALAOASATAUA;G@HAABAEzGAIBLAMANCRFSDUGYC;H@zAQEBGAHAIfNhOBUA;I@AADCjDDEAGAIALPMANzRASHTBVAXA;JAAEzOa;K@zBADAEiIBKAMANASETAYA;L@FADBACADzEMFAGAHAIFKALLMANAOHPASCTAUDVAWAYI;M@zADBBEtFBIHLAMRNAOCPJRASBUAWAYA;N@zABBACCDDEQFBGHHAICJAKALCMANAOBPAQARASNTEUAVAWAYAZA;O@JCADzEAFBHAIAKaLIMBNGPBRKSDTFVAZA;P@EAAEXGAHOIDKALzMAOJPGRBSBTAUBYA;QUz;R@zABBACADhEXFAGBHAICKDLCMCNDOBPARCSDTNUAVAWAYBZA;S@BACCAEzHCIJKALAMAODPDRASKTYUAYA;T@zAABACAEDHeIBLAMANAOAPARASATBUAWAYA;U@zBCCBDBEAGRIALaMANaPARuSWTY;V@AAAEzIEOA;W@zADBACADAESFAGAHAICKALEMANcPARASDTAWAYA;X@zCBElFAIGLAYA;Y@zAFEoFBHAIDMQNAOASG;Z@zAoBCEvICKBNHRKYB;;PA@AAABBCCDAEAGAHAIHJAKGLEMANGPBRzSeTFUBVAWAYHZA;BEROLRz;COz;E@IAZBACIDGECFAGAHAIAKALCNaOoPARzSCTIUAWAXAYA;FEGOMUz;GAz;H@GAKEXIzKALAMANAOEPARDSATBUAYDZA;I@AABBACGDDEUFAGBHAIAKALLMANXOBPBRxSJTzUAZA;KEzIj;LAYEzIEOIUCYD;MAGEzOB;NEzOA;O@AAACADAEAIFKELFMANzOFPBRXSWTCUFVBWJXAYA;P@BAFEtHAIILYOzRTUAYF;R@AAJEXIbOzUAYA;S@zABEAHAIAKAOATAYA;T@zALCAERHBIpLANAOARASCUDYB;UAABUCBDAEAFAGAHAIAKALOMANFPARuSBTzZA;WAzICRC;Y@zGARfTA;;QNEz;OUz;QSz;R@z;S@z;TTz;UAyCAEnIzODSAYA;;RA@CAABOCXDYEoFBGMHLIlJAKBLbMMNzOFPDRGSHTsUAVKWJYTZA;B@gAsEhIzLEOMSvUFYF;C@AAEEeHzIPLBOBTAUQYJ;D@zABEGHAIHLAMANAOARASIUAWAYA;E@zAPBACDDKEEFFGBHAICJAKALBMDNIOBPCQBRBSJTFUAVCWBYAZA;F@BACEzIALHOYRASAUU;G@HAKEzHDIPLAOHRAUCYH;H@BAzEDIBOJUBYB;I@BAMBLCYDDEmFFGQHAIAJAKALFMCNzOIPCQARASaTiUBVLWAXAZA;JAzEHOGUS;K@zAAEkFAHAICLAMGNHOASRTAYA;L@CAWBADzENIMOFSBUAWCYu;M@pAPEzFAHAIjLANAOaSOTAUFWAYO;N@zANCAEoFAIaMGNAODPASFTGWAYA;O@CAEBDCDDLEAFGGBHBIAJAKBLCMzNOODPRRASITHUdVJWLXAYFZA;P@JACEWHBIDLSNAOzROSCUAYA;QUz;R@CAKEeHBIzOpSAUIYg;S@zABCADAELHCICLAMAODPAQATLUBWAYA;T@zARBACAENFAGAHpIULBMANAOARBSKUHYI;U@BAABECbDIEQFAGCHAIVLQMRNPOAPIQARASzTZVAZA;V@BAyEzIUOAYA;WAzEAHCIjOBRA;XEz;Y@zAABAEAGAHAIALAMAOAPASATAWA;ZAzECIf;;SA@BABBBCEDBEAFBGAHAIzKDLRMPNNPARKSATFUEVHWHXAYf;BAzECHALAMAOCUBYI;C@AArEaHPIeLBOzRbSAUGYA;DAJEgIENAOzRA;E@zADBACDDJEKFAGAHAIAKALMMANIOAPBQARJSITDUAVCWAXAYA;FAQEUIzOkRAUvYY;GABIHOBRzUG;H@JAzBACADAEQFAGAHAIGKALAMBNAONPARATAUBVAYA;I@AAQBGCIDdEDFAGPHALUMFNzOqPAQARYSNTTUDVFWAXKZA;JOz;K@yAAEmIzLAMAOASCUCYD;LAzEiIHMAOHUBYK;M@IAzEIIcNAOXSAUMYA;N@AALEzIAOGUC;O@zAABACDDAEDFAIAJALJMVNpOCPBRHSATAUMVBWA;P@AAXEzHBIcLBOVRGSAUBYA;QUz;R@AAzEAIAOA;S@zAGEQFAHAIMLAMANAOBPARAUBVAWAYA;T@zANBACAEJFAHAIILBMANAOHPARNSDUBWAYA;U@AAFBaCzDCEGFUGEIFKALCMYNHPfRuSf;VEz;WAGEzIEOZUA;Y@tBACCEAICLBMDNKRzSV;;TA@CAABUCBDAEAFAGIHAIrKkLZMCNzOAPARQSBThUDVBWAXMYD;BAEEAOzRC;C@DAAHzIALAOARAUAYA;DOz;E@XAEBACADXECFAGAHAIAKALEMENRODPARzSPTCUAVAWAXAYAZA;FABEAIALAOBRKUz;GAzObRB;H@JAIBACADAEzFAGAHAIEJALAMANAODPAQARBSATAUAWAYBZA;I@AADBACHDAEJFDGAHAIAKALKMPNOOzPBQARBSETIUAVGZB;LADEzHAIBLAMAOAUAYl;MAFEzIBOP;NAAEzIEMATAUA;O@zAABACADAEAFAGBHAIAKALAMANBOCPARBSATAUAWBXAYA;PACEYIBLzOBUB;RAzEgIfLAOZUfYZ;S@zBACAEBHAIAKAMAOBPATAWAYA;T@AACEzHAIELVOCRASAUAYB;U@AAIBACADGEBFAGBHAIALAMCNGOAPARzSFTF;WAGEvIJOz;X@z;Y@zAABACAEAFAIALAPARASATA;Z@zEXID;;UA@GBACADBEAFAGCHAIBKBLzMANSRLSATEYA;B@EACBECFDCEEISJRLzMCOBSUTOUFVAYA;C@AACCEDAEQHzICKDLANAOARATLUAYA;D@TAgDEEfGzIJLAOARBSDUAYD;E@zAADEEDFALFNPPARCSLTAZA;F@AAeFzTAUA;G@AABEAGBHzIALAMBNARASAUA;H@EAZEEIz;I@AAACGDCEDLfNJOAPARVSJTzVDZA;JAz;K@AAAEzIAKBOARA;L@TALBACADzEEFBGAIBKALINAOAPARASCTLUAWAYB;M@WAJBzCFEiFAHAIGMDNAODPVRCSLTAUJVAYA;N@BAABACCDSEBFAGCHAICJAKALAMANAOAPAQARASBTzUAVAWAYA;O@jDAIANARYSATSUz;P@eAABAECHAIALAMAOzPJRBSATCUAWAYA;QUz;R@zAGBBCEDCEVFAGBHAIFKALAMANPOCPDQARBSKTGUAVAYC;S@zAJBBCAEmHBIFKALANCOAPAQASATUUBWAYA;T@zAABACADAEEFAGAHFICLAMANAOAPARASATBUBWAYB;UMzSz;VAzEzIz;X@HICUz;Y@zEFIFSD;Z@NALICOAZz;;VA@ABACADAGBHAIKJALhNzPARFSBTUUAWA;E@zAACADFEAGAHAIALBMANUPARoSHTBXAYA;I@CABBBCQDrEFGCIALqMANzOIPARGSRTNUCVAXAZA;O@ACDGAIzKGLMMAOAPARITDUuWIYB;REz;S@zHz;UEBLzSE;Y@zIH;;WABADAFAGCIBKBLFMANCRQSzTGVAXAYV;BAgEzODRN;CAzIM;D@zElIDLJNbOhRHSGYG;E@YAGBADFEIIBLRNNPARzSDTBVDYA;FIALAOAUz;GIzLE;HAQEgIzObYD;I@ACCDAEAFCGALeMANFPARASETzVAXAZA;K@zERIWSFWt;L@LABEzIDSIYG;M@GAzEz;N@zCADAEBFAIALARASBWAYA;O@NEBFAKALAMHNCODPARzTAUYVA;PRz;RAOEHIzOcUAYB;S@zAAEAHAIALAOAPATAYA;T@BECHzOBSB;UNz;WOz;Y@FEz;;XABACaDBGBLSMzNDSATO;CEzHOIDLGOARAUB;DRz;E@CCZDrMHNRRhSzTAUs;FOz;HARIGOz;I@AAABACDECGEIALCMFNEOERASJTzVA;LEzIZYz;MEz;ODCNTRz;PAAEzIBLDOTRFUA;QUz;SCzUZ;T@eAABAEzHOICOEReUBYJ;UAFLBRz;XIzXZ;Y@z;;YA@ABDGDLQMANERzSATAUAWA;B@NAzDAERIDLAORUA;CALEBHzIBLNOgUB;DAVDVEzIrOHRH;E@zAfBADJEAIALANAOARESJTMWA;FAGEBIBOGUz;GAzEMImMM;HEWOz;IEDNzSATA;L@BACEBICLBOzUAVB;M@AACBBEzIANBOAPDUA;NAzCADAEDICMAODTF;OFAKANARAUz;PEBHAIANAOERCSATz;R@AAyCADAEGIzNAOARDSATAUG;S@zABELHAIDMAOAPASATGUAWA;TAGEEHzIBODTA;UCzNz;VEz;WAEHzOH;X@z;ZEzIH;;ZA@EAABFCCDFECGAHDIALCMANDPARzTFVAZA;BAZIzOzUZ;E@aAFBOCEDzEEHAKPLDMCNZPCRZSDTAZA;GAz;HAz;I@GAeBICDDIELFAHAKDLKMHNZOzPGRATIZB;JOz;KARIz;LEzIVUD;MAzOR;NAzImOM;O@rAJBHHDNHPERzSATBUE;PAzEr;RAvExIPOz;SLz;THz;UAHBGIBMDPERzZE;VOz;Y@z;Z@BAzEBIeLGOAUAYA;;"

def letterList(element= None):
	if element == None:
		element= []
	letters= []
	for index in range(0, 27):
		letters.append(element)
	return letters

def addWord(letters, word):
	indexes= [0, 0]
	for letter in word.lower():
		indexes.append(ord(letter) - ord('a') + 1)
	indexes.append(0)
	for index in range(0, len(indexes) - 2):
		if len(letters[indexes[index]]) == 0:
			letters[indexes[index]]= letterList()
		if len(letters[indexes[index]][indexes[index + 1]]) == 0:
			letters[indexes[index]][indexes[index + 1]]= letterList(0)
		letters[indexes[index]][indexes[index + 1]][indexes[index + 2]]+= 1

def getLetter(letters, current, last):
	totalCount= 0
	for letter in letters[last][current]:
		totalCount+= letter
	if totalCount:
		position= random.randint(0, totalCount - 1)
		index= None
		for next in range(0, len(letters[last][current])):
			position-= letters[last][current][next]
			if position <= 0:
				return (last, current, next)
	return (last, current, 0)

kCountCharacters= "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
def pack(letters):
	results= []
	for last in range(0, len(letters)):
		if letters[last]:
			results.append(chr(last + ord('A') - 1))
			for current in range(0, len(letters[last])):
				if letters[last][current]:
					results.append(chr(current + ord('A') - 1))
					max= 0
					for count in letters[last][current]:
						if count > max:
							max= count
					for next in range(0, len(letters[last][current])):
						if letters[last][current][next]:
							results.append(chr(next + ord('A') - 1))
							count= letters[last][current][next] * (len(kCountCharacters) - 1) / max
							results.append(kCountCharacters[count])
					results.append(';')
			results.append(';')
	return "".join(results)

def unpack(string):
	index= 0
	results= letterList()
	while index < len(string) and string[index] != ';':
		last= ord(string[index]) - ord('A') + 1
		index+= 1
		if len(results[last]) == 0:
			results[last]= letterList()
		while index < len(string) and string[index] != ';':
			current= ord(string[index]) - ord('A') + 1
			index+= 1
			if len(results[last][current]) == 0:
				results[last][current]= letterList(0)
			while index < len(string) and string[index] != ';':
				next= ord(string[index]) - ord('A') + 1
				index+= 1
				count= kCountCharacters.find(string[index]) + 1
				index+= 1
				results[last][current][next]= count
			index+= 1 # skip ;
		index+= 1 # skip ;
	return results

def getWord(letters= None, maxSize= 10, minSize= 6):
	if not letters:
		letters= unpack(kWordTablePacked)
	position= (0, 0, 0)
	characters= []
	while True:
		position= getLetter(letters, position[2], position[1])
		if not position[2]:
			break
		characters.append(chr(position[2] + ord('a') - 1))
		if len(characters) >= 10:
			break
	if len(characters) <  minSize:
		return getWord(letters, maxSize, minSize)
	return "".join(characters)

if __name__ == "__main__":
	WordPattern= re.compile(r"[a-zA-Z]+")
	for word in range(0, 25):
		print getWord()
	letters= letterList()
	for arg in sys.argv[1:]:
		try:
			for word in WordPattern.finditer(open(arg, "r").read()):
				addWord(letters, word.group(0))
		except:
			pass
	letters= unpack(pack(letters))
	print pack(letters)
	for word in range(0, 25):
		print getWord(letters)
