export default function TableChartWidget({ data }) {

  if (!data || data.length === 0) {
    return <div>Немає даних для відображення</div>;
  }

  const columns = Object.keys(data[0]);

  return (
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #f3f4f6', color: '#6b7280' }}>
            {columns.map((colName, index) => (
              <th key={index} style={{ padding: '0.75rem', textTransform: 'capitalize' }}>
                {colName.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} style={{ borderBottom: '1px solid #f3f4f6' }}>

              {columns.map((colName, colIndex) => (
                <td key={colIndex} style={{ padding: '0.75rem' }}>
                  {row[colName]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
  );
}
