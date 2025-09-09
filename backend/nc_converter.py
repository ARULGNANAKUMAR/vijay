import xarray as xr
import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetCDFConverter:
    """Converter for ARGO NetCDF files to CSV format"""

    def __init__(self, upload_folder='uploads', output_folder=None):
        self.upload_folder = upload_folder
        self.output_folder = output_folder or upload_folder

        # Create directories if they don't exist
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

    def convert_single_file(self, nc_file_path, output_path=None):
        """Convert a single NetCDF file to CSV"""
        try:
            logger.info(f"Converting {nc_file_path}")

            # Open NetCDF file
            with xr.open_dataset(nc_file_path) as ds:
                # Convert to DataFrame
                df = ds.to_dataframe().reset_index()

                # Clean up DataFrame (remove NaN-only columns, etc.)
                df = self._clean_dataframe(df)

                # Generate output path if not provided
                if not output_path:
                    base_name = os.path.splitext(os.path.basename(nc_file_path))[0]
                    output_path = os.path.join(self.output_folder, f"{base_name}.csv")

                # Save to CSV
                df.to_csv(output_path, index=False)

                result = {
                    'success': True,
                    'input_file': nc_file_path,
                    'output_file': output_path,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'file_size_mb': os.path.getsize(output_path) / (1024 * 1024),
                    'processed_at': datetime.utcnow().isoformat()
                }

                logger.info(f"Successfully converted to {output_path}")
                return result

        except Exception as e:
            logger.error(f"Error converting {nc_file_path}: {str(e)}")
            return {
                'success': False,
                'input_file': nc_file_path,
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }

    def batch_convert(self, input_folder, file_pattern='*.nc'):
        """Convert all NetCDF files in a folder"""
        import glob

        # Find all NetCDF files
        nc_files = glob.glob(os.path.join(input_folder, file_pattern))
        logger.info(f"Found {len(nc_files)} NetCDF files to convert")

        results = []
        for nc_file in nc_files:
            result = self.convert_single_file(nc_file)
            results.append(result)

        # Summary statistics
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        logger.info(f"Conversion complete: {successful} successful, {failed} failed")

        return {
            'total_files': len(results),
            'successful': successful,
            'failed': failed,
            'results': results,
            'summary': self._generate_summary(results)
        }

    def _clean_dataframe(self, df):
        """Clean and optimize DataFrame"""
        # Remove columns that are entirely NaN
        df = df.dropna(axis=1, how='all')

        # Convert object columns to appropriate types where possible
        for col in df.select_dtypes(include=['object']).columns:
            try:
                # Try to convert to numeric
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass

        # Round numeric columns to reasonable precision
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].round(6)

        return df

    def _generate_summary(self, results):
        """Generate summary statistics from conversion results"""
        successful_results = [r for r in results if r['success']]

        if not successful_results:
            return {'message': 'No successful conversions'}

        total_rows = sum(r.get('rows', 0) for r in successful_results)
        total_size_mb = sum(r.get('file_size_mb', 0) for r in successful_results)
        avg_columns = np.mean([r.get('columns', 0) for r in successful_results])

        return {
            'total_rows_converted': total_rows,
            'total_output_size_mb': round(total_size_mb, 2),
            'average_columns_per_file': round(avg_columns, 1),
            'processing_time': datetime.utcnow().isoformat()
        }

    def get_nc_file_info(self, nc_file_path):
        """Get detailed information about a NetCDF file"""
        try:
            with xr.open_dataset(nc_file_path) as ds:
                info = {
                    'filename': os.path.basename(nc_file_path),
                    'file_size_mb': os.path.getsize(nc_file_path) / (1024 * 1024),
                    'dimensions': dict(ds.dims),
                    'coordinates': list(ds.coords),
                    'data_variables': list(ds.data_vars),
                    'global_attributes': dict(ds.attrs),
                    'time_range': self._get_time_range(ds),
                    'spatial_bounds': self._get_spatial_bounds(ds)
                }
                return info

        except Exception as e:
            return {
                'filename': os.path.basename(nc_file_path),
                'error': str(e)
            }

    def _get_time_range(self, ds):
        """Extract time range from dataset"""
        try:
            if 'time' in ds.coords:
                time_coord = ds.coords['time']
                return {
                    'start': str(time_coord.min().values),
                    'end': str(time_coord.max().values),
                    'count': len(time_coord)
                }
            elif 'JULD' in ds.coords:  # ARGO Julian day
                juld = ds.coords['JULD']
                return {
                    'start': str(juld.min().values),
                    'end': str(juld.max().values),
                    'count': len(juld)
                }
        except:
            pass
        return None

    def _get_spatial_bounds(self, ds):
        """Extract spatial bounds from dataset"""
        try:
            bounds = {}

            # Check for latitude
            lat_vars = ['latitude', 'lat', 'LATITUDE']
            for var in lat_vars:
                if var in ds.coords or var in ds.data_vars:
                    lat_data = ds[var]
                    bounds['latitude'] = {
                        'min': float(lat_data.min().values),
                        'max': float(lat_data.max().values)
                    }
                    break

            # Check for longitude
            lon_vars = ['longitude', 'lon', 'LONGITUDE']
            for var in lon_vars:
                if var in ds.coords or var in ds.data_vars:
                    lon_data = ds[var]
                    bounds['longitude'] = {
                        'min': float(lon_data.min().values),
                        'max': float(lon_data.max().values)
                    }
                    break

            return bounds if bounds else None

        except:
            return None

def main():
    """Command line interface for NetCDF converter"""
    import argparse

    parser = argparse.ArgumentParser(description='Convert ARGO NetCDF files to CSV')
    parser.add_argument('input', help='Input NetCDF file or directory')
    parser.add_argument('--output', help='Output directory (default: same as input)')
    parser.add_argument('--info', action='store_true', help='Show file info only')

    args = parser.parse_args()

    converter = NetCDFConverter(output_folder=args.output)

    if args.info:
        info = converter.get_nc_file_info(args.input)
        print(json.dumps(info, indent=2))
    elif os.path.isfile(args.input):
        result = converter.convert_single_file(args.input)
        print(json.dumps(result, indent=2))
    elif os.path.isdir(args.input):
        results = converter.batch_convert(args.input)
        print(json.dumps(results, indent=2))
    else:
        print(f"Error: {args.input} is not a valid file or directory")

if __name__ == "__main__":
    main()
