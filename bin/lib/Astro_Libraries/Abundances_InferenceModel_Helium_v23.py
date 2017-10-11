from pyneb                  import atomicData, RecAtom, Atom
from collections            import OrderedDict
from uncertainties.unumpy   import nominal_values, std_devs
from Reddening_Corrections  import ReddeningLaws
from lib.Astro_Libraries.Nebular_Continuum  import NebularContinuumCalculator
from lib.ssp_functions.ssp_synthesis_tools import ssp_fitter
from numpy                  import array, loadtxt, genfromtxt, isnan, arange, insert, concatenate, mean, std, power, exp, zeros, square, empty, percentile, random, median, ones, isnan, sum as np_sum
import pymc as pymc2
import pymc3 
from timeit import default_timer as timer

class Import_model_data(ReddeningLaws):

    def __init__(self):

        #Import sub classes
        ReddeningLaws.__init__(self)

        self.Hydrogen_CollCoeff_TableAddress    = '/home/vital/workspace/dazer/bin/lib/Astro_Libraries/Neutral_Hydrogen_Collisional_Correction_coef.txt'
        self.Helium_CollCoeff_TableAddress      = '/home/vital/workspace/dazer/bin/lib/Astro_Libraries/Neutral_Helium_Collisional_Correction_coef.txt'
        self.Helium_OpticalDepth_TableAddress   = '/home/vital/workspace/dazer/bin/lib/Astro_Libraries/Helium_OpticalDepthFunction_Coefficients.txt'
        
        #Declare Hydrogen and Helium lines for the analysis
        self.posHydrogen_Lines      = ['H1_4102A',      'H1_4340A', 'H1_6563A']
        self.Hydrogen_Wavelengths   = array([4101.742,  4340.471,   6562.819])
        
        self.posHelium_Lines        = ['He1_3889A',  'He1_4026A',    'He1_4387A',    'He1_4471A',    'He1_4686A',    'He1_4714A',    'He1_4922A',   'He1_5876A',    'He1_6678A',   'He1_7065A',    'He1_7281A',    'He1_10830A']
        self.Helium_Wavelengths     = array([3889.0,  4026.0,         4387.0,         4471.0,         4686.0,         4714.0,         4922.0,         5876.0,         6678.0,       7065.0,         7281.0,        10830.0])

        self.posSII_Lines           = ['S2_6716A', 'S2_6731A'] 
        self.SII_Wavelenths         = array([6716.44, 6730.81])
        
        self.posSIII_Lines          = ['S3_6312A', 'S3_9069A', 'S3_9531A']
        self.SIII_Wavelenths        = array([6312.06, 9068.6, 9531.1])      

    def import_table_data(self, Address, Columns):
        
        Imported_Array  = genfromtxt(Address, dtype=float, usecols = Columns, skip_header = 2).T
        Datarray = Imported_Array[:,~isnan(Imported_Array).all(0)]
                
        return Datarray
     
    def import_coll_coeff_table(self, HydrogenLines, HeliumLines):
        
        Data_dict = OrderedDict()
                
        for i in range(len(HydrogenLines)):
            
            Line            = HydrogenLines[i]
            Data_Columns    = [0 + 3*i, 1 + 3*i, 2 + 3*i]
            Data_dict[Line] = self.import_table_data(self.Hydrogen_CollCoeff_TableAddress, Data_Columns)
                    
        return Data_dict
     
    def import_optical_depth_coeff_table(self, HeliumLines):
        
        Data_dict = OrderedDict()
        
        for i in range(len(HeliumLines)):
            
            Line = HeliumLines[i]
            
            if Line != self.H13889A_label:
                Data_dict[Line] = loadtxt(self.Helium_OpticalDepth_TableAddress, dtype = float, skiprows = 2, usecols = (i,))
                
            else:
                Data_dict[self.He3889_label] = loadtxt(self.Helium_OpticalDepth_TableAddress, dtype = float, skiprows = 2, usecols = (i,))
            
        return Data_dict

    def load_synthetic_data(self, model):
        
        #Dictionary with data from the object
        self.obj_data = dict()
        
        #Physical parameters from the object
        self.obj_data['z_star']         = 0.0154
        self.obj_data['sigma_star']     = 1.254
        self.obj_data['Av_star']        = 0.754            

        self.Hbeta_Eqw                  = 250.0
        self.Hbeta_EqwErr               = 12.5
        self.Hbeta_hlambda              = 1.0

        self.obj_data['y_plusplus']     = 0.0
        self.obj_data['y_plus']         = 0.085
        self.obj_data['n_e']            = 120.0
        self.obj_data['tau']            = 1.0
        self.obj_data['T_low']          = 15500.0
        self.obj_data['T_high']         = 1.0807 * self.obj_data['T_low'] - 0.0846
        self.obj_data['cHbeta']         = 0.1
        self.obj_data['xi']             = 1.0  
        self.obj_data['TSIII']          = 15000.0
        self.obj_data['TSIII_error']    = 700
        self.obj_data['nSII']           = 150.0
        self.obj_data['nSII_error']     = 50.0

        self.obj_data['O2_abund']       = 0.00025
        self.obj_data['O3_abund']       = 0.00075

        self.obj_data['S2_abund']       = 0.000015
        self.obj_data['S3_abund']       = 0.000055

        #Lines available from the object WARNING: It would be good to load these details from a text/pandas format
        self.obj_data['H_labels']       = ['H1_4102A',          'H1_4340A',         'H1_6563A']
        self.obj_data['H_wave']         = array([4101.742,    4340.471,       6562.819])
        self.obj_data['H_Eqw']          = array([50.0,        50.0,           300.0])
        self.obj_data['H_EqwErr']       = array([1.0,         1.0,            14])
        self.obj_data['H_hlambda']      = array([1.0,         1.0,            1.0])
        self.obj_data['H_pyneb_code']   = array(['6_2',       '5_2',          '3_2'])

        self.obj_data['He_labels']      = ['He1_3889A',         'He1_4026A',    'He1_4471A',    'He1_5876A', 'He1_6678A',   'He1_7065A',    'He1_10830A']
        self.obj_data['He_wave']        = array([ 3889.0,       4026.0,         4471.0,         5876.0,      6678.0,        7065.0,         10830.0])
        self.obj_data['He_Eqw']         = array([10.0,          10.0,           10.0,           10.0,        10.0,          10.0,           10.0])
        self.obj_data['He_EqwErr']      = array([1.0,           1.0,            1.0,            1.0,         1.0,           1.0,            1.0])
        self.obj_data['He_hlambda']     = array([1.0,           1.0,            1.0,            1.0,         1.0,           1.0,            1.0])
        self.obj_data['He_pyneb_code']  = array(['3889.0',      '4026.0',       '4471.0',       '5876.0',    '6678.0',      '7065.0',       '10830.0'])

        self.obj_data['S2_labels']      = ['S2_6716A', 'S2_6731A']
        self.obj_data['S2_wave']        = array([6716.44, 6730.81])
        self.obj_data['S2_pyneb_code']  = array([6716, 6730])
        self.obj_data['S3_labels']      = ['S3_6312A', 'S3_9069A', 'S3_9531A']
        self.obj_data['S3_wave']        = array([6312.06, 9068.6, 9531.1])
        self.obj_data['S3_pyneb_code']  = array([6312, 9069, 9531])

        self.obj_data['O2_labels']      = ['O2_3726A', 'O2_3729A']
        self.obj_data['O2_wave']        = array([3726.032, 3728.815])
        self.obj_data['O2_pyneb_code']  = array([3726, 3729])
        self.obj_data['O3_labels']      = ['O3_4363A', 'O3_4959A', 'O3_5007A']
        self.obj_data['O3_wave']        = array([4363.21, 4958.911, 5006.843])
        self.obj_data['O3_pyneb_code']  = array([4363, 4959, 5007])

        return

    def load_obs_data(self, lines_df, obj_series, extension_treat = '', Deblend_Check = True):
        
        #Empty dictionary to store the data
        self.obj_data = {}

        #--Define HBeta values in advance
        idx_Hbeta                       = lines_df.index == 'H1_4861A'
        self.Hbeta_Flux                 = nominal_values(lines_df.loc[idx_Hbeta, 'line_Flux'].values)
        self.Hbeta_error                = std_devs(lines_df.loc[idx_Hbeta, 'line_Flux'].values)
        self.Hbeta_Eqw                  = nominal_values(lines_df.loc[idx_Hbeta, 'line_Eqw'].values) #WARNING: in cases with removed stellar this eqw gives trouble
        self.Hbeta_EqwErr               = std_devs(lines_df.loc[idx_Hbeta, 'line_Eqw'].values)
        self.Hbeta_hlambda              = nominal_values(lines_df.loc[idx_Hbeta, 'Continuum_Median'].values)

        #Load Hydrogen lines data in the dictionary
        idcs_H                          = lines_df.index.isin(self.posHydrogen_Lines)   #Hydrogen lines
        self.obj_data['H_labels']       = lines_df.loc[idcs_H].index.values
        self.obj_data['H_Ions']         = lines_df.loc[idcs_H, 'Ion'].values
        self.obj_data['H_Flux']         = nominal_values(lines_df.loc[idcs_H, 'line_Flux'].values)
        self.obj_data['H_error']        = std_devs(lines_df.loc[idcs_H, 'line_Flux'].values)
        self.obj_data['H_wave']         = lines_df.loc[idcs_H, 'TheoWavelength'].values
        self.obj_data['H_Eqw']          = nominal_values(lines_df.loc[idcs_H, 'line_Eqw'].values) #WARNING: in cases with removed stellar this eqw gives trouble
        self.obj_data['H_EqwErr']       = std_devs(lines_df.loc[idcs_H, 'line_Eqw'].values)
        self.obj_data['H_hlambda']      = nominal_values(lines_df.loc[idcs_H, 'Continuum_Median'].values)
        self.obj_data['H_pyneb_code']   = lines_df.loc[idcs_H, 'Ion'].str[lines_df.loc[idcs_H, 'Ion'].str.find('_'):]

        #Load Helium lines data
        idcs_He                         = lines_df.index.isin(self.posHelium_Lines)
        self.obj_data['He_labels']      = lines_df.loc[idcs_He].index.values
        self.obj_data['He_Ions']        = lines_df.loc[idcs_He, 'Ion'].values
        self.obj_data['He_Flux']        = nominal_values(lines_df.loc[idcs_He, 'line_Flux'].values)
        self.obj_data['He_error']       = std_devs(lines_df.loc[idcs_He, 'line_Flux'].values)
        self.obj_data['He_wave']        = lines_df.loc[idcs_He, 'TheoWavelength'].values
        self.obj_data['He_Eqw']         = nominal_values(lines_df.loc[idcs_He, 'line_Eqw'].values) #WARNING: in cases with removed stellar this eqw gives trouble
        self.obj_data['He_EqwErr']      = std_devs(lines_df.loc[idcs_He, 'line_Eqw'].values)
        self.obj_data['He_hlambda']     = nominal_values(lines_df.loc[idcs_He, 'Continuum_Median'].values)
        self.obj_data['He_pyneb_code']  = lines_df.loc[idcs_He].index.str[lines_df.loc[idcs_He].index.str.find('_')+1:-1]

        #Load physical parameters data       
        Thigh_key                       = obj_series['T_high']
        self.obj_data['TOIII']          = obj_series[Thigh_key + extension_treat].nominal_value
        self.obj_data['TOIII_error']    = obj_series[Thigh_key + extension_treat].std_dev
        self.obj_data['nSII']           = obj_series['neSII' + extension_treat].nominal_value
        self.obj_data['nSII_error']     = obj_series['neSII' + extension_treat].std_dev
        self.obj_data['cHbeta_obs']     = obj_series['cHbeta' + extension_treat].nominal_value

        #Check if He1_3889A is on the observations (In the current analysis it appears as 'H1_3889A')
        if 'H1_3889A' in lines_df.index:
            idx_He3889A = (lines_df.index == 'H1_4861A')
            
            #This should be calculated using the error
            He3889A_debFlux = self.deblend_He3889A(Te = self.obj_data['TOIII'], ne = self.obj_data['nSII'], cHbeta = self.obj_data['cHbeta_obs'])
    
            insert(self.obj_data['He_labels'],      0, lines_df.loc[idx_He3889A].index.values)
            insert(self.obj_data['He_Ions'],        0, lines_df.loc[idx_He3889A, 'Ion'].values)
            insert(self.obj_data['He_Flux'],        0, He3889A_debFlux.nominal_value)
            insert(self.obj_data['He_error'],       0, He3889A_debFlux.std_dev)
            insert(self.obj_data['He_wave'],        0, lines_df.loc[idx_He3889A, 'TheoWavelength'].values)
            insert(self.obj_data['He_Eqw'],         0, nominal_values(lines_df.loc[idx_He3889A, 'line_Eqw'].values)) #WARNING: in cases with removed stellar this eqw gives trouble
            insert(self.obj_data['He_EqwErr'],      0, std_devs(lines_df.loc[idx_He3889A, 'line_Eqw'].values))
            insert(self.obj_data['He_hlambda'],     0, nominal_values(lines_df.loc[idx_He3889A, 'Continuum_Median'].values))
            insert(self.obj_data['He_pyneb_code'],  0, lines_df.loc[idx_He3889A].index.str[lines_df.loc[idx_He3889A].index.str.find('_')+1:-1])
        
        return

    def prepare_run_data(self, norm_by_Hbeta = False, deblend_Check = True, red_curve = 'G03_average', Rv = 3.4):

        #Variables to speed up the code
        self.nHydrogen              = len(self.obj_data['H_labels'])
        self.nHydrogen_range        = arange(self.nHydrogen)
        
        self.nHelium                = len(self.obj_data['He_labels'])
        self.nHelium_range          = arange(self.nHelium)

        self.obj_data['nS2']        = len(self.obj_data['S2_labels'])
        self.obj_data['nS2_range']  = arange(self.obj_data['nS2'])

        self.obj_data['nS3']        = len(self.obj_data['S3_labels'])
        self.obj_data['nS3_range']  = arange(self.obj_data['nS3'])

        self.obj_data['nO2']        = len(self.obj_data['O2_labels'])
        self.obj_data['nO2_range']  = arange(self.obj_data['nO2'])

        self.obj_data['nO3']        = len(self.obj_data['O3_labels'])
        self.obj_data['nO3_range']  = arange(self.obj_data['nO3'])

        self.nTotal = self.nHydrogen + self.nHelium
       
        #Load the reddening parameters
        H_xX        = self.reddening_Xx(self.obj_data['H_wave'], red_curve, Rv)
        He_xX       = self.reddening_Xx(self.obj_data['He_wave'], red_curve, Rv)
        S2_xX       = self.reddening_Xx(self.obj_data['S2_wave'], red_curve, Rv)
        S3_xX       = self.reddening_Xx(self.obj_data['S3_wave'], red_curve, Rv)
        O2_xX       = self.reddening_Xx(self.obj_data['O2_wave'], red_curve, Rv)
        O3_xX       = self.reddening_Xx(self.obj_data['O3_wave'], red_curve, Rv)
        self.Hbeta_xX = self.reddening_Xx(array([self.Hbeta_wave]), red_curve, Rv)[0]
        
        #Dictionary with the vectors
        self.data_dic = {'Emissivity_H_vector'  : zeros(self.nHydrogen),
                         'Emissivity_He_vector' : zeros(self.nHelium),
                         'Emissivity_S2_vector' : zeros(self.obj_data['nS2']),
                         'Emissivity_S3_vector' : zeros(self.obj_data['nS3']),
                         'Emissivity_O2_vector' : zeros(self.obj_data['nO2']),
                         'Emissivity_O3_vector' : zeros(self.obj_data['nO3']),                         
                         'Kalpha_vector'        : zeros(self.nHydrogen),
                         'ftau_He_vector'       : zeros(self.nHelium),
                         'flambda_H_vector'     : H_xX/self.Hbeta_xX - 1.0,
                         'flambda_He_vector'    : He_xX/self.Hbeta_xX - 1.0,    
                         'flambda_S2_vector'    : S2_xX/self.Hbeta_xX - 1.0,
                         'flambda_S3_vector'    : S3_xX/self.Hbeta_xX - 1.0,    
                         'flambda_O2_vector'    : O2_xX/self.Hbeta_xX - 1.0,
                         'flambda_O3_vector'    : O3_xX/self.Hbeta_xX - 1.0}    

        #Normalize the fluxes by Hbeta if necessary
        if norm_by_Hbeta: 
            self.obj_data['H_Flux']   = self.obj_data['H_Flux']     / self.Hbeta_Flux
            self.obj_data['He_Flux']  = self.obj_data['He_Flux']    / self.Hbeta_Flux
            self.obj_data['H_error']  = self.obj_data['H_error']    / self.Hbeta_Flux
            self.obj_data['He_error'] = self.obj_data['He_error']   / self.Hbeta_Flux

            self.obj_data['S2_Flux']  = self.obj_data['S2_Flux']    / self.Hbeta_Flux
            self.obj_data['S3_Flux']  = self.obj_data['S3_Flux']    / self.Hbeta_Flux
            self.obj_data['S2_error'] = self.obj_data['S2_error']   / self.Hbeta_Flux
            self.obj_data['S3_error'] = self.obj_data['S3_error']   / self.Hbeta_Flux

            self.obj_data['O2_Flux']  = self.obj_data['O2_Flux']    / self.Hbeta_Flux
            self.obj_data['O3_Flux']  = self.obj_data['O3_Flux']    / self.Hbeta_Flux
            self.obj_data['O2_error'] = self.obj_data['O2_error']   / self.Hbeta_Flux
            self.obj_data['O3_error'] = self.obj_data['O3_error']   / self.Hbeta_Flux
       
        return

class Continua_FluxCalculation(ssp_fitter):

    def __init__(self):
        
        ssp_fitter.__init__(self)
        
class Nebular_FluxCalculation(NebularContinuumCalculator):
    
    def __init__(self):
        
        NebularContinuumCalculator.__init__(self)

    def nebular_Cont(self, wave_obs, z, cHbeta, Te, y_plus, y_plusplus, Halpha_Flux):
        
        wave_obs_rest   = wave_obs / (1.0 + z)
         
        neb_gCont       = self.calculate_neb_gCont(wave_obs_rest, Te, y_plus, y_plusplus)
         
        neb_int_norm    = self.gCont_calibration(wave_obs_rest, Te, Halpha_Flux, neb_gCont)
                     
        neb_xX          = self.reddening_Xx(wave_obs_rest, 'G03_average', 3.4)
        flambda_neb     = neb_xX/self.Hbeta_xX - 1.0
         
        neb_flux_norm   = neb_int_norm * power(10, -1 * flambda_neb * cHbeta)        
        
        return neb_flux_norm

    def calculate_nebular_SED(self, wave_obs, z, cHbeta, Te, y_plus, y_plusplus, Halpha_Flux):
        
        wave_obs_rest   = wave_obs / (1.0 + z)
         
        neb_gCont       = self.calculate_neb_gCont(wave_obs_rest, Te, y_plus, y_plusplus)
         
        neb_int_norm    = self.gCont_calibration(wave_obs_rest, Te, Halpha_Flux, neb_gCont)
                     
        neb_xX          = self.reddening_Xx(wave_obs_rest, 'G03_average', 3.4)
        flambda_neb     = neb_xX/self.Hbeta_xX - 1.0
         
        neb_flux_norm   = neb_int_norm * power(10, -1 * flambda_neb * cHbeta)   
                
        nebular_SED = {}
        nebular_SED['neb_gCont']        = neb_gCont        
        nebular_SED['neb_int_norm']     = neb_int_norm                    
        nebular_SED['neb_xX']           = neb_xX
        nebular_SED['flambda_neb']      = flambda_neb        
        nebular_SED['neb_flux_norm']    = neb_flux_norm        
        
        return nebular_SED
                   
class Recombination_FluxCalibration():
    
    def __init__(self):
            
        #Define indexes and labels to speed up the code
        self.Hbeta_label            = 'H1_4861A'
        self.Hbeta_wave             = 4862.683
        self.Hbeta_pynebCode        = '4_2'
        self.H13889A_label          = 'H1_3889A'          
        self.He3889_label           = 'He1_3889A'
        self.He3889_Check           = None
        
        #Set up the right emissivities
        #atomicData.setDataFile('he_i_rec_Pal12-Pal13.fits')
        
        #Declare pyneb Hydrogen and Helium atoms to calculate emissivities
        self.H1                     = RecAtom('H', 1)
        self.He1                    = RecAtom('He', 1) 
    
        #Make sure we are using the right helium emissivities
        print '--Helium emissivities: '
        self.He1.printSources()

        #Import collisional coefficients table #We add the Hbeta to get its coefficients
        self.Coef_Kalpha_dict       = self.import_coll_coeff_table(self.posHydrogen_Lines + [self.Hbeta_label], None)

        #Import Optical depth function
        self.Coef_ftau_dict         = self.import_optical_depth_coeff_table(self.posHelium_Lines) 

    def H_alphaCalc(self, Te, ne, xi, cHbeta, idx_Halpha = 2):
        
        t4 = Te / 10000.0
        
        Hbeta_Kalpha        = self.Kalpha_Ratio_H(T_4 = t4, H_label = self.Hbeta_label)
        Hbeta_emis          = self.H1.getEmissivity(Te, ne, label = self.Hbeta_pynebCode)

        Halpha_Kalpha       = self.Kalpha_Ratio_H(T_4 = t4, H_label = self.obj_data['H_labels'][idx_Halpha])
        Emissivity_Halpha   = self.H1.getEmissivity(Te, ne, label = self.obj_data['H_pyneb_code'][idx_Halpha])
        
        emis_module         = Emissivity_Halpha / Hbeta_emis
        
        CR_Module           = (1.0 + 0.0001* xi * Halpha_Kalpha) / (1.0 + 0.0001* xi * Hbeta_Kalpha)
        
        f_module            = power(10, -1 * self.data_dic['flambda_H_vector'][idx_Halpha] * cHbeta)
        
        Halpha_Flux         = emis_module * CR_Module * f_module * self.Hbeta_Flux

        return Halpha_Flux

    def H_theoFlux(self, Te, ne, xi, cHbeta):
        
        #Hydrogen calculation parameters
        self.calculate_H_params(Te, ne)
        
        #Hbeta parameters
        Hbeta_emis      = self.H1.getEmissivity(Te, ne, label = self.Hbeta_pynebCode)
        Hbeta_Kalpha    = self.Kalpha_Ratio_H(T_4 = Te/10000.0, H_label = self.Hbeta_label)
        
        #Calculate the emissivities for each of the lines for the given temperature and density
        emis_module     = self.data_dic['Emissivity_H_vector'] / Hbeta_emis
                
        #Calculate the Collisional excitation fraction
        CR_Module       = (1.0 + 0.0001* xi * self.data_dic['Kalpha_vector']) / (1.0 + 0.0001* xi * Hbeta_Kalpha)
                
        #Calculate the reddening component
        f_module        = power(10, -1 * self.data_dic['flambda_H_vector'] * cHbeta)

        #Calculate theoretical Hydrogen flux for each emission line
        H_Flux          = emis_module * CR_Module * f_module
                     
        return H_Flux

    def He_theoFlux(self, Te, ne, tau, xi, cHbeta, y_plus):
        
        #Helium calculation parameters
        self.calculate_He_params(Te, ne, tau)
        
        #Hbea kalpha
        Hbeta_emis      = self.H1.getEmissivity(Te, ne, label = self.Hbeta_pynebCode)
        Hbeta_Kalpha    = self.Kalpha_Ratio_H(T_4 = Te/10000.0, H_label = self.Hbeta_label)
        
        #Calculate the emissivities for each of the lines for the given temperature and density
        emis_module = self.data_dic['Emissivity_He_vector'] / Hbeta_emis
                
        #Calculate the collisional excitation fraction
        CR_Module   = 1 / (1.0 + 0.0001* xi * Hbeta_Kalpha)

        #Calculate the reddening component
        f_module    = power(10, -1 *  self.data_dic['flambda_He_vector'] * cHbeta)
             
        #Calculate theoretical helium flux for the line
        He_Flux     = y_plus * emis_module * self.data_dic['ftau_He_vector'] * CR_Module * f_module

        return He_Flux
                                                                    
    def calculate_H_params(self, Te, ne):    
        
        #Calculate in advance the T_4 parameter
        T_4 = Te / 10000.0
        
        #Calculate the hbeta parameters
        #self.Hbeta_Kalpha   = self.Kalpha_Ratio_H(T_4 = T_4, H_label = self.Hbeta_label)
        #self.Hbeta_emis     = self.H1.getEmissivity(Te, ne, label = self.Hbeta_pynebCode)

        #Calculate physical parameters for Hydrogen lines
        for i in self.nHydrogen_range:
            self.data_dic['Emissivity_H_vector'][i] = self.H1.getEmissivity(Te, ne, label = self.obj_data['H_pyneb_code'][i])
            self.data_dic['Kalpha_vector'][i]       = self.Kalpha_Ratio_H(T_4 = T_4, H_label = self.obj_data['H_labels'][i])
                        
        return 
        
    def calculate_He_params(self, Te, ne, tau):
    
        #Calculate in advance the T_4 parameter
        T_4 = Te / 10000.0
            
        #Calculate physical parameters for Helium lines
        for i in self.nHelium_range:
            self.data_dic['Emissivity_He_vector'][i]    = self.He1.getEmissivity(Te, ne, label = self.obj_data['He_pyneb_code'][i])
            self.data_dic['ftau_He_vector'][i]          = self.OpticalDepth_He(tau = tau, T_4 = T_4, ne = ne, He_label = self.obj_data['He_labels'][i])    
                    
        return
                          
    def Kalpha_Ratio_H(self, T_4, H_label):
                      
        K_alpha_Ratio   = sum(self.Coef_Kalpha_dict[H_label][0] * exp(self.Coef_Kalpha_dict[H_label][1] / T_4) * power(T_4, self.Coef_Kalpha_dict[H_label][2]))
        
        return K_alpha_Ratio

    def OpticalDepth_He(self, tau, T_4, ne, He_label):
                        
        f_tau   = 1 + (tau/2) * (self.Coef_ftau_dict[He_label][0] + (self.Coef_ftau_dict[He_label][1] + self.Coef_ftau_dict[He_label][2]*ne + self.Coef_ftau_dict[He_label][3]*ne*ne) * T_4)

        return f_tau

class Collisional_FluxCalibration(Import_model_data):
    
    def __init__(self):
                
        #Set atomic data
        atomicData.setDataFile('s_iii_coll_HRS12.dat')
        
        #Atoms to fit the data
        self.ionDict        = {}
        self.ionDict['S2']  = Atom('S', 2)
        self.ionDict['S3']  = Atom('S', 3) 
        self.ionDict['Ar3'] = Atom('Ar', 3)
        self.ionDict['Ar4'] = Atom('Ar', 4) 
        self.ionDict['O2']  = Atom('O', 2)
        self.ionDict['O3']  = Atom('O', 3)
        
    def coll_Flux(self, ion, Te, ne, cHbeta, ionic_abund):
        
        #Calculate Hbeta emissivity for this ion temperatre
        Hbeta_emis      = self.H1.getEmissivity(Te, ne, label = self.Hbeta_pynebCode)

        #Ions emissivities by Hbeta emissivity
        emis_module     = self.metal_emis(ion, Te, ne) / Hbeta_emis
                
        #Reddening factor
        f_module        = power(10, -1 * self.data_dic['flambda_{}_vector'.format(ion)] * cHbeta)

        #Metals flux
        metal_flux      = ionic_abund * emis_module * f_module
        
        return metal_flux
    
    def metal_emis(self, ion, Te, ne):
                
        ion_emis    = self.ionDict[ion]
        pyneb_code  = '{}_pyneb_code'.format(ion)
        vector_emis =  self.data_dic['Emissivity_{}_vector'.format(ion)]
        
        for i in self.obj_data['n' + ion + '_range']:    
            vector_emis[i] = ion_emis.getEmissivity(Te, ne, wave = self.obj_data[pyneb_code][i])
            
        return vector_emis
        
class Inference_AbundanceModel(Import_model_data, Collisional_FluxCalibration, Recombination_FluxCalibration, Continua_FluxCalculation, Nebular_FluxCalculation):

    def __init__(self):

        #Import tools to load data
        Import_model_data.__init__(self)
        Continua_FluxCalculation.__init__(self)
        Collisional_FluxCalibration.__init__(self)
        Recombination_FluxCalibration.__init__(self)
        Nebular_FluxCalculation.__init__(self)
                
    def calculate_synthFluxes(self, model, verbose = True):
          
        #Get physical parameters from model HII region
        self.load_synthetic_data(model = model)
        
        #Physical parameters for the nebular continua calculation
        self.load_neb_constants()

        #-------Prepare emission lines data
        self.prepare_run_data(norm_by_Hbeta = False, deblend_Check=False)
        
        #Recombination features                    
        self.obj_data['H_Flux']     = self.H_theoFlux(self.obj_data['T_low'], self.obj_data['n_e'], self.obj_data['xi'], self.obj_data['cHbeta'])
        self.obj_data['He_Flux']    = self.He_theoFlux(self.obj_data['T_high'], self.obj_data['n_e'], self.obj_data['tau'], self.obj_data['xi'], self.obj_data['cHbeta'], self.obj_data['y_plus'])
        self.obj_data['H_error']    = self.obj_data['H_Flux'] * 0.01
        self.obj_data['He_error']   = self.obj_data['He_Flux'] * 0.02
        
        #Collisinal excited features
        self.obj_data['S2_Flux']    = self.coll_Flux('S2', self.obj_data['T_low'], self.obj_data['n_e'], self.obj_data['cHbeta'], self.obj_data['S2_abund'])
        self.obj_data['S3_Flux']    = self.coll_Flux('S3', self.obj_data['T_low'], self.obj_data['n_e'], self.obj_data['cHbeta'], self.obj_data['S3_abund'])
        self.obj_data['O2_Flux']    = self.coll_Flux('O2', self.obj_data['T_low'], self.obj_data['n_e'], self.obj_data['cHbeta'], self.obj_data['O2_abund'])
        self.obj_data['O3_Flux']    = self.coll_Flux('O3', self.obj_data['T_high'], self.obj_data['n_e'], self.obj_data['cHbeta'], self.obj_data['O3_abund'])
        self.obj_data['S2_error']   = self.obj_data['S2_Flux'] * 0.02
        self.obj_data['S3_error']   = self.obj_data['S3_Flux'] * 0.02
        self.obj_data['O2_error']   = self.obj_data['O2_Flux'] * 0.02
        self.obj_data['O3_error']   = self.obj_data['O3_Flux'] * 0.02

        #Combined fluxes to speed up the process
        self.H_He_Obs_Flux          = concatenate([self.obj_data['H_Flux'], self.obj_data['He_Flux']])                        
        self.H_He_Obs_Error         = concatenate([self.obj_data['H_error'], self.obj_data['He_error']])  
        self.S2_S3_Obs_Flux         = concatenate([self.obj_data['S2_Flux'], self.obj_data['S3_Flux']])                        
        self.S2_S3_Obs_Error        = concatenate([self.obj_data['S2_error'], self.obj_data['S3_error']]) 
        self.O2_O3_Obs_Flux         = concatenate([self.obj_data['O2_Flux'], self.obj_data['O3_Flux']])                        
        self.O2_O3_Obs_Error        = concatenate([self.obj_data['O2_error'], self.obj_data['O3_error']]) 

        #-------Prepare stellar continua

        #Load stellar libraries
        default_Starlight_file      = '/home/vital/Starlight/Dani_Bases_Extra.txt'
        default_Starlight_folder    = '/home/vital/Starlight/Bases/'
        default_Starlight_coeffs    = '/home/vital/Starlight/Bases/coeffs_sync.txt'  
        
        ssp_lib_dict                = self.load_stellar_bases('starlight', default_Starlight_folder, default_Starlight_file, resample_int=1, resample_range = (3600, 6900), norm_interval = (5100,5150))
        
        #Generate synthetic observation using default values        
        self.stellar_SED            = self.calculate_synthStellarSED(self.obj_data['Av_star'], self.obj_data['z_star'], self.obj_data['sigma_star'], default_Starlight_coeffs, ssp_lib_dict, (4000, 6900))
        
        #-------Prepare nebular continua
        self.Hbeta_Flux             = 1e4 #This is the zanstra calibration factor which we are multipliying by the emissivity ratio
        
        Halpha_Flux                 = self.obj_data['H_Flux'][-1] * self.Hbeta_Flux / self.stellar_SED['normFlux_stellar']
        self.Halpha_norm            = Halpha_Flux
        
        self.nebular_SED            = self.calculate_nebular_SED(self.stellar_SED['stellar_wave_resam'], self.obj_data['z_star'], self.obj_data['cHbeta'], self.obj_data['T_low'], self.obj_data['y_plus'], self.obj_data['y_plusplus'], Halpha_Flux)
                
        #Redshift limits for the object
        z_max_ssp                   = (self.stellar_SED['stellar_wave_resam'][0] / ssp_lib_dict['basesWave_resam'][0]) - 1.0
        z_min_ssp                   = (self.stellar_SED['stellar_wave_resam'][-1] / ssp_lib_dict['basesWave_resam'][-1]) - 1.0
        self.z_max_ssp_limit        = round(z_max_ssp - 0.001, 3)
        self.z_min_ssp_limit        = z_min_ssp
        
        #Saving data required for the fit
        #--Declaring parameters used in the fit
        if '_neb' not in model:
            obs_flux_norm           = self.stellar_SED['stellar_flux_norm']
        else:
            print '-------------------BINGO'
            obs_flux_norm           = self.stellar_SED['stellar_flux_norm'] + self.nebular_SED['neb_flux_norm']
                   
        self.obj_data['normFlux_obs']           = self.stellar_SED['normFlux_stellar']
        self.obj_data['obs_wave_resam']         = self.stellar_SED['stellar_wave_resam'] 
        self.obj_data['obs_flux_norm']          = obs_flux_norm
        self.obj_data['obs_flux_norm_masked']   = self.obj_data['obs_flux_norm'] * self.stellar_SED['int_mask']
        self.obj_data['basesWave_resam']        = ssp_lib_dict['basesWave_resam'] 
        self.obj_data['bases_flux_norm']        = ssp_lib_dict['bases_flux_norm']
        self.obj_data['int_mask']               = self.stellar_SED['int_mask']
        self.obj_data['obs_fluxEr_norm']        = self.stellar_SED['stellar_fluxEr_norm']
        
        if verbose:
            print '\nInput Parameters:'
            print '-y_plus',    self.obj_data['y_plus']
            print '-n_e',       self.obj_data['n_e']
            print '-T_low',     self.obj_data['T_low']
            print '-T_high',    self.obj_data['T_high']
            print '-cHbeta',    self.obj_data['cHbeta']
            print '-tau',       self.obj_data['tau']
            print '-xi',        self.obj_data['xi']
            print '-TOIII',     self.obj_data['TSIII'],'+/-',self.obj_data['TSIII_error']
            print '-nSII',      self.obj_data['nSII'],'+/-',self.obj_data['nSII_error']
            print '\n-S2_abund',self.obj_data['S2_abund']
            print '-S3_abund',  self.obj_data['S3_abund']
            print '-O2_abund',  self.obj_data['O2_abund']
            print '-O3_abund',  self.obj_data['O3_abund']
    
            print '\n-z_star',  self.obj_data['z_star']
            print '-sigma_star',self.obj_data['sigma_star']
            print '-Av_star',   self.obj_data['Av_star']
            
            print '\n-Wavelength ranges:'
            print '--Observation:', self.obj_data['obs_wave_resam'][0], self.obj_data['obs_wave_resam'][-1]
            print '--Bases:', ssp_lib_dict['basesWave_resam'][0], ssp_lib_dict['basesWave_resam'][-1]
            print '--z min:', self.z_min_ssp_limit
            print '--z max:', self.z_max_ssp_limit
            print '--z true:', self.obj_data['z_star']
    
            print '\nHydrogen emissivities'
            for i in self.nHydrogen_range:
                print '-{} {}'.format(self.obj_data['H_labels'][i], self.obj_data['H_Flux'][i])
    
            print '\nHelium emissivities'
            for i in self.nHelium_range:
                print '-{} {}'.format(self.obj_data['He_labels'][i], self.obj_data['He_Flux'][i])
    
            print '\nS2 emissivities'
            for i in self.obj_data['nS2_range']:
                print '-{} {}'.format(self.obj_data['S2_labels'][i], self.obj_data['S2_Flux'][i])
    
            print '\nS3 emissivities'
            for i in self.obj_data['nS3_range']:
                print '-{} {}'.format(self.obj_data['S3_labels'][i], self.obj_data['S3_Flux'][i])
    
            print '\nO2 emissivities'
            for i in self.obj_data['nO2_range']:
                print '-{} {}'.format(self.obj_data['O2_labels'][i], self.obj_data['O2_Flux'][i])
    
            print '\nO3 emissivities'
            for i in self.obj_data['nO3_range']:
                print '-{} {}'.format(self.obj_data['O3_labels'][i], self.obj_data['O3_Flux'][i])
                 
        return

    def He_O_S_nebStellar_model(self):
        
        y_plus      =   pymc2.Uniform(          'y_plus',       0.050,                      0.15)
        S2_abund    =   pymc2.Uniform(          'S2_abund',     0.000001,                   0.15)
        S3_abund    =   pymc2.Uniform(          'S3_abund',     0.000001,                   0.15)
        O2_abund    =   pymc2.Uniform(          'O2_abund',     0.000001,                   0.15)
        O3_abund    =   pymc2.Uniform(          'O3_abund',     0.000001,                   0.15)                        
        ne          =   pymc2.TruncatedNormal(  'ne',           self.obj_data['nSII'],      self.obj_data['nSII_error']**-2,    a = 0.0 ,   b = 1000.0)
        tau         =   pymc2.TruncatedNormal(  'tau',          0.75,                       0.5**-2,    a = 0.0,    b = 7.0)
        cHbeta      =   pymc2.TruncatedNormal(  'cHbeta',       0.15,                       0.05**-2,   a = 0.0,    b = 3.0)
        xi          =   pymc2.TruncatedNormal(  'xi',           1,                          200**-2,    a = 0.0,    b = 1000.0)
        T_He        =   pymc2.TruncatedNormal(  'T_He',         self.obj_data['TSIII'],      self.obj_data['TSIII_error']**-2,    a = 5000.0 ,   b = 50000.0)
        T_low       =   pymc2.TruncatedNormal(  'T_low',        self.obj_data['TSIII'],     self.obj_data['TSIII_error']**-2,    a = 5000.0 ,   b = 50000.0)
        #z_star     =   pymc2.Uniform('z_star',    self.z_min_ssp_limit, self.z_max_ssp_limit)
        Av_star     =   pymc2.Uniform('Av_star',   0.0, 5.00)
        sigma_star  =   pymc2.Uniform('sigma_star',0.0, 5.00)
               
        @pymc2.deterministic
        def H_alpha_model(Te=T_low, ne=ne, xi=xi, cHbeta=cHbeta):
            return self.H_alphaCalc(Te, ne, xi, cHbeta, idx_Halpha=2)
        
        @pymc2.deterministic
        def nebular_continua(z_star=self.obj_data['z_star'], cHbeta=self.obj_data['cHbeta'], Te=self.obj_data['T_low'], y_plus=y_plus, y_plusplus=0.0, Halpha_Flux=self.Halpha_norm):
                   
            neb_flux_norm = self.nebular_Cont(self.obj_data['obs_wave_resam'], z_star, cHbeta, Te, y_plus, y_plusplus, Halpha_Flux)

            return neb_flux_norm
        
        @pymc2.deterministic
        def ssp_coefficients(z_star=self.obj_data['z_star'], Av_star=Av_star, sigma_star=sigma_star, nebular_flux=nebular_continua):
            
            self.nebular_flux_masked = nebular_flux * self.obj_data['int_mask']
            
            obsFlux_non_neb = self.obj_data['obs_flux_norm_masked'] - self.nebular_flux_masked            
            
            ssp_grid_i = self.physical_SED_model(self.obj_data['basesWave_resam'], self.obj_data['obs_wave_resam'], self.obj_data['bases_flux_norm'], Av_star, z_star, sigma_star, 3.4)
            
            self.ssp_grid_i_masked = (self.obj_data['int_mask'] * ssp_grid_i.T).T
            
            ssp_coeffs_norm = self.ssp_fitting(self.ssp_grid_i_masked, obsFlux_non_neb)
            
            return ssp_coeffs_norm        

        @pymc2.deterministic
        def stellar_continua_calculation(ssp_coeffs = ssp_coefficients):
            
            flux_sspFit_norm = np_sum(ssp_coeffs.T * self.ssp_grid_i_masked, axis=1)
            
            theo_continuum = flux_sspFit_norm + self.nebular_flux_masked
            
            return theo_continuum
               
        @pymc2.deterministic #Calculate Hydrogen theoretical flux
        def H_model(Te=T_He, ne=ne, xi=xi, cHbeta=cHbeta):
            return self.H_theoFlux(Te=Te, ne=ne, xi=xi, cHbeta=cHbeta)
           
        @pymc2.deterministic #Calculate Helium theoretical flux 
        def He_model(Te=T_He, ne=ne, tau=tau, xi=xi, cHbeta=cHbeta, y_plus=y_plus):
            return self.He_theoFlux(Te=1.0807 * Te - 0.0846, ne=ne,  tau=tau, xi=xi, cHbeta=cHbeta, y_plus = y_plus)

        @pymc2.deterministic #Calculate S2 theoretical flux 
        def S2_model(ion='S2', Te=T_low, ne=ne, cHbeta=cHbeta, ionic_abund=S2_abund):
            return self.coll_Flux('S2',Te,ne,cHbeta,ionic_abund)

        @pymc2.deterministic #Calculate S3 theoretical flux 
        def S3_model(ion='S3', Te=T_low, ne=ne, cHbeta=cHbeta, ionic_abund=S3_abund):
            return self.coll_Flux('S3',Te,ne,cHbeta,ionic_abund)

        @pymc2.deterministic #Calculate O2 theoretical flux 
        def O2_model(ion='O2', Te=T_low, ne=ne, cHbeta=cHbeta, ionic_abund=O2_abund):
            return self.coll_Flux('O2',Te,ne,cHbeta,ionic_abund)

        @pymc2.deterministic #Calculate O3 theoretical flux 
        def O3_model(ion='O3', Te=T_low, ne=ne, cHbeta=cHbeta, ionic_abund=O3_abund):
            return self.coll_Flux('O3',1.0807 * Te - 0.0846,ne,cHbeta,ionic_abund)

        @pymc2.deterministic #Combine theoretical fluxes into a single array
        def H_He_TheoFlux(H_Ftheo=H_model, He_Ftheo=He_model):
            H_He_Theo_Flux = empty(self.nTotal)
            H_He_Theo_Flux[:self.nHydrogen] = H_Ftheo[:]
            H_He_Theo_Flux[self.nHydrogen:] = He_Ftheo[:]
            return H_He_Theo_Flux

        @pymc2.deterministic #Combine theoretical fluxes into a single array
        def S2_S3_TheoFlux(S2_Ftheo=S2_model, S3_Ftheo=S3_model):
            S2_S3_Theo_Flux = empty(5)
            S2_S3_Theo_Flux[:2] = S2_Ftheo[:]
            S2_S3_Theo_Flux[2:] = S3_Ftheo[:]
            return S2_S3_Theo_Flux
 
        @pymc2.deterministic #Combine theoretical fluxes into a single array
        def O2_O3_TheoFlux(O2_Ftheo=O2_model, O3_Ftheo=O3_model):
            O2_O3_TheoFlux = empty(5)
            O2_O3_TheoFlux[:2] = O2_Ftheo[:]
            O2_O3_TheoFlux[2:] = O3_Ftheo[:]
            return O2_O3_TheoFlux 

        @pymc2.stochastic(observed=True) #Likelihood
        def likelihood_ssp(value = self.obj_data['obs_flux_norm_masked'], StellarCont_TheoFlux=stellar_continua_calculation, sigmaContinuum=self.obj_data['obs_fluxEr_norm']):
            chi_F = sum(square(StellarCont_TheoFlux - value) / square(sigmaContinuum))
            return - chi_F / 2
 
        @pymc2.stochastic(observed=True) #Likelihood
        def Likelihood_model_Recomb(value = self.H_He_Obs_Flux, H_He_TheoFlux = H_He_TheoFlux, sigmaLines = self.H_He_Obs_Error):
            chi_F = sum(square(H_He_TheoFlux - value) / square(sigmaLines))
            return - chi_F / 2

        @pymc2.stochastic(observed=True) #Likelihood
        def Likelihood_model_S(value = self.S2_S3_Obs_Flux, S2_S3_TheoFlux = S2_S3_TheoFlux, sigmaLines = self.S2_S3_Obs_Error):
            chi_F = sum(square(S2_S3_TheoFlux - value) / square(sigmaLines))
            return - chi_F / 2

        @pymc2.stochastic(observed=True) #Likelihood
        def Likelihood_model_O(value = self.O2_O3_Obs_Flux, O2_O3_TheoFlux = O2_O3_TheoFlux, sigmaLines = self.O2_O3_Obs_Error):
            chi_F = sum(square(O2_O3_TheoFlux - value) / square(sigmaLines))
            return - chi_F / 2
        
        @pymc2.deterministic() #Deterministic method to track the evolution of the chi:
        def chiSq_ssp(obs = self.obj_data['obs_flux_norm_masked'], StellarCont_TheoFlux=stellar_continua_calculation, sigmaContinuum=self.obj_data['obs_fluxEr_norm']):
            chi_F = sum(square(StellarCont_TheoFlux - obs) / square(sigmaContinuum))
            return - chi_F / 2  

        @pymc2.deterministic() #Deterministic method to track the evolution of the chi:
        def ChiSq_Recomb(H_He_ObsFlux = self.H_He_Obs_Flux, H_He_TheoFlux = H_He_TheoFlux, sigmaLines = self.H_He_Obs_Error):
            chi_F = sum(square(H_He_TheoFlux - H_He_ObsFlux) / square(sigmaLines))
            return - chi_F / 2
 
        @pymc2.deterministic() #Deterministic method to track the evolution of the chi:
        def ChiSq_S(S2_S3_Obs_Flux = self.S2_S3_Obs_Flux, S2_S3_TheoFlux = S2_S3_TheoFlux, sigmaLines = self.S2_S3_Obs_Error):
            chi_F = sum(square(S2_S3_TheoFlux - S2_S3_Obs_Flux) / square(sigmaLines))
            return - chi_F / 2
 
        @pymc2.deterministic() #Deterministic method to track the evolution of the chi:
        def ChiSq_O(O2_O3_Obs_Flux = self.O2_O3_Obs_Flux, O2_O3_TheoFlux = O2_O3_TheoFlux, sigmaLines = self.O2_O3_Obs_Error):
            chi_F = sum(square(O2_O3_TheoFlux - O2_O3_Obs_Flux) / square(sigmaLines))
            return - chi_F / 2

        return locals()
  
class Run_MCMC(Inference_AbundanceModel, ssp_fitter):

    def __init__(self):
        
        #Import parent classes
        Inference_AbundanceModel.__init__(self)
        self.pymc_stats_keys = ['mean','95% HPD interval','standard deviation','mc error','quantiles','n']
  
    def select_inference_model(self, model):

        if model == '_stellar':
            self.inf_dict = self.stellar_continua_fitting()
        
        elif model == '_neb_stellar':
            self.inf_dict = self.nebular_stellar_continua_fitting()
        
        elif model == '_He_S_O_neb_stellar':
            self.inf_dict = self.He_O_S_nebStellar_model()
        
        elif model == 'ssp_synthesis_pymc3':
            self.inf_dict = self.stellar_continua_fitting_pymc3()
                 
    def run_pymc2(self, db_address, iterations = 10000, burn_phase = 1500, thining=2, variables_list = None):
        
#         #Ideal cond1: iter=30000, burn=5000, thin=10
#         #Ideal cond2: iter=10000, burn=1500, thin=2
# 
#         #Prefit:
#         self.MAP_Model  = pymc2.MAP(self.inf_dict)
#                         
#         #Launch sample
#         self.pymc2_M    = pymc2.MCMC(self.MAP_Model.variables, db = 'pickle', dbname =  db_address)
#         self.pymc2_M.sample(iter=iterations, burn=burn_phase, thin=thining)
#         
#         #Save the output csv mean data
#         if variables_list != None:
#             print '--Saving results in csv'
#             self.csv_address = db_address + '_Parameters'
#             self.pymc2_M.write_csv(self.csv_address, variables=variables_list)
#             
#         #Print again the             
#         self.display_run_data(self.MAP_Model, variables_list)
# 
#         #Close the database
#         self.pymc2_M.db.close()  
        
        #Prefit:
        print '\n--Starting Fmin_powell prefit'
        start = timer()
        self.MAP_Model  = pymc2.MAP(self.inf_dict)
        self.MAP_Model.fit(method = 'fmin_powell')
        end = timer()
        print 'Fmin_powell interval', (end - start) 

         
        #Print prefit data
        self.display_run_data(self.MAP_Model, variables_list)
                 
        #Launch sample
        self.pymc2_M  = pymc2.MCMC(self.MAP_Model.variables, db = 'pickle', dbname =  db_address)
        self.pymc2_M.sample(iter=iterations, burn=burn_phase, thin=thining)
         
        #Save the output csv mean data
        if variables_list != None:
            print '--Saving results in csv'
            self.csv_address = db_address + '_Parameters'
            self.pymc2_M.write_csv(self.csv_address, variables=variables_list)
             
        #Print again the             
        self.display_run_data(self.MAP_Model, variables_list)
 
        #Close the database
        self.pymc2_M.db.close()       

    def load_pymc_database_manual(self, db_address, burning = 0):
                
        #Load the pymc output textfile database
        pymc_database = pymc2.database.pickle.load(db_address)
        
        #Create a dictionaries with the traces and statistics
        traces_dic = {}
        stats_dic = OrderedDict()
        
        #This variable contains all the traces from the MCMC (stochastic and deterministic)
        traces_list = pymc_database.trace_names[0] 
    
        #Get statistics from the run    
        for trace in traces_list:
            stats_dic[trace]    = OrderedDict()
            trace_array = pymc_database.trace(trace)[burning:]
            traces_dic[trace]   = trace_array
            
            stats_dic[trace]['mean']                    = mean(trace_array)
            stats_dic[trace]['median']                  = median(trace_array)
            stats_dic[trace]['standard deviation']      = std(trace_array)
            stats_dic[trace]['n']                       = trace_array.shape[0]
            stats_dic[trace]['16th_p']                  = percentile(trace_array, 16)
            stats_dic[trace]['84th_p']                  = percentile(trace_array, 84)
            stats_dic[trace]['95% HPD interval']        = (stats_dic[trace]['16th_p'], stats_dic[trace]['84th_p'])
            stats_dic[trace]['trace']                   = trace_array
            
        #Generate a MCMC object to recover all the data from the run
        dbMCMC = pymc2.MCMC(traces_dic, pymc_database)
        
        return dbMCMC, stats_dic  

    def run_pymc3(self, iterations = 10000, burn_phase = 1500, thining=2,  db_address=None, variables_list = None, prefit_method = 'fmin_powell', start_conditions = None):
        
        #Import the inference model
        pymc3_model = self.inf_dict
             
        #Prefit:
        if prefit_method != None:
            #Check if initial conditions are provided
            if start_conditions != None:
                print '\n--Starting prefit'
                start_conditions = pymc3.find_MAP(model = pymc3_model)
            #Print prefit data
            self.display_run_data(start_conditions, variables_list)
        
        #Default saving path
        if db_address != None:
            db = pymc3.backends.Text(db_address)
        else:
            db = None
        
        #Run the model
        with pymc3_model:
           
            #Instantiate the sampler
            step = pymc3.Slice()    
            
            #Run sampler
            trace = pymc3.sample(iterations, step=step, start=start_conditions, trace=db)
            
        #Save the output data using a clasical approach    
        with open(db_address + '.pkl', 'wb') as pickle_trace:
            pickle.dump({'model': pymc3_model, 'trace': trace}, pickle_trace)
                            
    def display_run_data(self, database, variables_list):
        
        for param in variables_list:
            param_entry = getattr(database, param, None)
            if param_entry is not None:
                print '-{} {}'.format(param, param_entry.value)

    def load_pymc_database(self, db_address):
                
        #Load the pymc output textfile database
        pymc_database = pymc2.database.pickle.load(db_address)
                
        #Create a dictionaries with the traces and statistics
        traces_dic = {}
        stats_dic = OrderedDict()
        
        #This variable contains all the traces from the MCMC (stochastic and deterministic)
        traces_list = pymc_database.trace_names[0]
        print 'Estas variables', traces_list
        print pymc_database.trace('stellar_continua_calculation').stats()['quantiles'][2.5] 
    
        #Get statistics from the run    
        for trace in traces_list:
            stats_dic[trace] = OrderedDict()
            traces_dic[trace] = pymc_database.trace(trace)
            
            for stat in self.pymc_stats_keys: 
                stats_dic[trace][stat] = pymc_database.trace(trace).stats()[stat] 
    
            trace_array = pymc_database.trace(trace)[:] 
            stats_dic[trace]['16th_p'] = percentile(trace_array, 16)
            stats_dic[trace]['84th_p'] = percentile(trace_array, 84)    
    
        #Generate a MCMC object to recover all the data from the run
        dbMCMC = pymc2.MCMC(traces_dic, pymc_database)
        
        return dbMCMC, stats_dic                                                                                                 

    def load_pymc_pickle(self, db_address):
        
        #Load the pymc output textfile database
        pymc_database = pymc2.database.pickle.load(db_address)
        
        print pymc_database.trace_names[0]
        
        #You can recover the data using these commands
        #pymc_database.trace('stellar_continua_calculation').stats()['mean']
        #pymc_database.trace('stellar_continua_calculation').stats()['quantiles'][2.5] 
        
        return pymc_database